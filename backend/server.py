from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import uuid
import shutil
import fitz
import io
from PIL import Image
from google import genai
from google.genai import types


import vector_store # using my own file for vectors

# loading env stuff
# MY_ROOT = Path(__file__).parent
load_dotenv(str(Path(__file__).parent) + "/.env") # this loads the env variables from the folder

MANUAL_FOLDER = str(Path(__file__).parent.parent) + "/manuals"
UPLOAD_FOLDER = str(Path(__file__).parent.parent) + "/uploads"

if not os.path.exists(MANUAL_FOLDER):
    os.makedirs(MANUAL_FOLDER)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = FastAPI()
api = APIRouter(prefix="/api")

# AI MODELS
my_model = None
def get_embedding_model():
    global my_model
    if my_model == None:
        from sentence_transformers import SentenceTransformer
        my_model = SentenceTransformer("all-MiniLM-L6-v2")
    return my_model

def get_embeds(text_list):
    mod = get_embedding_model()
    # converting to numpy so it works
    return mod.encode(text_list, convert_to_numpy=True, normalize_embeddings=True)

# gemini client setup
key = os.environ.get("GEMINI_API_KEY")
gem_client = genai.Client(api_key=key) if key != None else None

def call_gemini_api(prompt_str, pic_list=None):
    if gem_client == None:
        raise Exception("API KEY NOT FOUND OMG")
    
    msg_parts = []
    msg_parts.append(prompt_str)
    
    if pic_list != None:
        for p in pic_list:
            b = io.BytesIO()
            p.save(b, format="JPEG") # compress it to jpeg
            msg_parts.append(types.Part.from_bytes(data=b.getvalue(), mime_type="image/jpeg"))
            
    ans = gem_client.models.generate_content(model="gemini-flash-latest", contents=msg_parts)
    return ans.text

# image things
def process_img_bytes(b_data, f_name):
    p = UPLOAD_FOLDER + "/" + f_name
    file = open(p, "wb")
    file.write(b_data)
    file.close()
    return p

def read_img(p):
    i = Image.open(p)
    if i.mode != "RGB":
        i = i.convert("RGB")
    return i

# pdf logic
def read_pdf_file(p):
    pdf = fitz.open(p)
    fulltext = ""
    for page in pdf:
        fulltext = fulltext + page.get_text()
    pdf.close()
    return fulltext

def make_chunks(txt):
    words = txt.split(" ") # split by space
    all_chunks = []
    index = 0
    while index < len(words):
        temp_chunk = " ".join(words[index:index+500])
        if temp_chunk.strip() != "":
            all_chunks.append(temp_chunk)
        index = index + 500 - 50 # overlap
    return all_chunks


# API ENDPOINTS
@api.get("/")
def home():
    # just checking if it works
    return {"message": "hello world from backend"}

@api.get("/status")
def get_status():
    status = vector_store.check_index()
    return {"has_index": status}

@api.post("/upload-pdf")
async def do_pdf_upload(file: UploadFile = File(...)):
    print("uploading pdf started...", flush=True)
    filename = file.filename.lower()
    if filename.endswith(".pdf") == False:
        raise HTTPException(400, "bro its not a pdf")
    
    new_path = MANUAL_FOLDER + "/" + str(uuid.uuid4()) + "_" + file.filename
    f = open(new_path, "wb")
    shutil.copyfileobj(file.file, f)
    f.close()
    
    try:
        print("reading pdf file...", flush=True)
        t = read_pdf_file(new_path)
        print("making chunks...", flush=True)
        c = make_chunks(t)
        if len(c) == 0:
            raise Exception("no text found")
        print("getting embeddings (this might take time)...", flush=True)
        v = get_embeds(c)
        print("making faiss index...", flush=True)
        vector_store.make_the_index(v, c)
        print("pdf upload complete!", flush=True)
    except Exception as error_msg:
        print("ERROR IN PDF:", error_msg, flush=True)
        raise HTTPException(500, "Failed to do it: " + str(error_msg))
    
    return {"filename": file.filename, "chunks": len(c)}

@api.post("/upload-image")
async def do_img_upload(file: UploadFile = File(...)):
    # print("image upload started")
    extension = os.path.splitext(file.filename)[1].lower()
    valid = [".png", ".jpg", ".jpeg", ".webp"]
    
    is_valid = False
    for v in valid:
        if extension == v:
            is_valid = True
            
    if is_valid == False:
        raise HTTPException(400, "bad image format")
        
    random_name = str(uuid.uuid4()) + extension
    bytes_data = await file.read()
    saved_loc = process_img_bytes(bytes_data, random_name)
    return {"path": saved_loc, "name": random_name, "original": file.filename}

@api.post("/ask")
async def do_ask(question: str = Form(...), image_paths: str = Form("")):
    # print("someone asked:", question)
    if question.strip() == "":
        raise HTTPException(400, "you need a question")
        
    imgs = []
    if image_paths != "":
        paths = image_paths.split(",")
        for p in paths:
            if p.strip() != "":
                imgs.append(p)
                
    try:
        # get context
        q_v = get_embeds([question])[0]
        ctx = vector_store.search_stuff(q_v, 4)
        
        ctx_text = ""
        for counter, item in enumerate(ctx):
            ctx_text = ctx_text + "[" + str(counter+1) + "] " + item["text"] + "\n\n"
            
        if ctx_text == "":
            ctx_text = "No manual uploaded."
            
        p = "You are a technical support assistant. Use the manual excerpts and image (if given) to help the user.\n\nManual context:\n" + ctx_text + "\n\nUser question: " + question + "\n\nGive step-by-step troubleshooting instructions. Be clear and specific. If an image is provided, mention what you see in it."
        
        # load images for gemini
        loaded_imgs = []
        for i in imgs:
            loaded_imgs.append(read_img(i))
            
        ans = call_gemini_api(p, loaded_imgs if len(loaded_imgs) > 0 else None)
        
    except Exception as errr:
        print("ask failed!!", errr)
        raise HTTPException(500, "Failed to get answer: " + str(errr))
        
    return {"answer": ans, "context": ctx}

@api.post("/reset")
def do_reset():
    vector_store.clear_all()
    return {"ok": True}

app.include_router(api)

# cors stuff so react can talk to it
try:
    origins = os.environ.get("CORS_ORIGINS", "*").split(",")
except:
    origins = ["*"]
    
app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
