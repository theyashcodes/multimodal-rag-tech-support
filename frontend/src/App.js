import { useState, useRef } from "react";
import axios from "axios";
import "./App.css";

// var API = `${process.env.REACT_APP_BACKEND_URL}/api`;
var API = "https://multimodal-rag-tech-support.onrender.com/api" // using the live backend url

function App() {
  // state for pdf stuff
  var [pdf_file_name, set_pdf_file_name] = useState("");
  var [numChunks, setNumChunks] = useState(0);
  var [isUploading, setIsUploading] = useState(false);
  
  // state for images
  var [myImages, setMyImages] = useState([]);
  
  // state for chat
  var [q, setQ] = useState("");
  var [isThinking, setIsThinking] = useState(false);
  var [all_msgs, setAllMsgs] = useState([]);
  var [errorMsg, setErrorMsg] = useState("");

  var pdfRef1 = useRef();
  var imgRef2 = useRef();

  // function to do pdf upload
  const doUploadPDF = async (e) => {
    console.log("upload pdf clicked!!");
    var the_file = e.target.files[0];
    if (the_file == null) {
      return;
    }
    setErrorMsg(""); // clear old error
    setIsUploading(true);
    
    var form_data = new FormData();
    form_data.append("file", the_file);
    
    try {
      var res = await axios.post(API + "/upload-pdf", form_data);
      console.log("pdf uploaded ok:", res.data);
      set_pdf_file_name(res.data.filename);
      setNumChunks(res.data.chunks);
    } catch (e) {
      console.log("error!!!", e);
      if (e.response && e.response.data && e.response.data.detail) {
        setErrorMsg(e.response.data.detail);
      } else {
        setErrorMsg("Failed to upload PDF");
      }
    }
    setIsUploading(false);
  };

  // function to upload images
  const doUploadImages = async (event) => {
    console.log("image upload started!");
    var selectedFiles = Array.from(event.target.files);
    if (selectedFiles.length == 0) {
      return;
    }
    setErrorMsg("");
    
    // loop through all files
    for (var i=0; i<selectedFiles.length; i++) {
      var f = selectedFiles[i];
      var fd = new FormData();
      fd.append("file", f);
      
      try {
        var res = await axios.post(API + "/upload-image", fd);
        var pUrl = URL.createObjectURL(f);
        // add to array
        setMyImages((old) => {
          return [...old, { path: res.data.path, name: res.data.original, url: pUrl }];
        });
      } catch (err) {
        console.log("img err", err);
        setErrorMsg("Failed to upload image :(");
      }
    }
  };

  // function to delete image
  const deleteImg = (index) => {
    var newArr = [];
    for (var i=0; i<myImages.length; i++) {
      if (i != index) {
        newArr.push(myImages[i]);
      }
    }
    setMyImages(newArr);
  };

  // main chat ask function
  const doAsk = async () => {
    if (q.trim() == "") {
      return; // do nothing
    }
    setErrorMsg("");
    setIsThinking(true);
    
    var temp_q = q;
    setQ(""); // clear input box
    
    var u_msg = { role: "user", text: temp_q, images: myImages.map((img) => img.url) };
    setAllMsgs((old) => [...old, u_msg]);
    
    var fd2 = new FormData();
    fd2.append("question", temp_q);
    
    // get paths of images as comma separated string
    var imgPaths = "";
    for (var j=0; j<myImages.length; j++) {
      imgPaths = imgPaths + myImages[j].path + ",";
    }
    fd2.append("image_paths", imgPaths);
    
    try {
      var r = await axios.post(API + "/ask", fd2);
      console.log("got answer!");
      setAllMsgs((old) => {
        return [...old, { role: "assistant", text: r.data.answer, context: r.data.context }];
      });
    } catch (e) {
      console.log("chat err", e);
      setErrorMsg("Failed to get answer: " + (e.response?.data?.detail || "unknown error"));
    }
    setIsThinking(false);
  };

  // function to reset everything
  const doReset = async () => {
    console.log("resetting...");
    await axios.post(API + "/reset");
    set_pdf_file_name("");
    setNumChunks(0);
    setMyImages([]);
    setAllMsgs([]);
  };

  // HTML starts here
  return (
    <div style={{minHeight: "100vh", backgroundColor: "#0a0a0a", color: "#f5f5f5", fontFamily: "sans-serif"}}>
      <div style={{maxWidth: "1152px", margin: "0 auto", padding: "24px 24px"}}>
        
        {/* HEADER DIV */}
        <header style={{marginBottom: "32px", display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid #262626", paddingBottom: "24px"}}>
          <div>
            <h1 style={{fontSize: "30px", fontWeight: "600", margin: "0"}} data-testid="app-title">Multi-modal RAG Support</h1>
            <p style={{fontSize: "14px", color: "#a3a3a3", marginTop: "4px"}}>Upload a manual, share images, ask questions.</p>
          </div>
          <button
            onClick={doReset}
            style={{fontSize: "14px", padding: "6px 12px", borderRadius: "6px", border: "1px solid #404040", backgroundColor: "transparent", color: "white", cursor: "pointer"}}
            data-testid="reset-btn"
          >
            Reset
          </button>
        </header>

        {/* MAIN LAYOUT DIV */}
        <div style={{display: "grid", gridTemplateColumns: "1fr 2fr", gap: "24px"}}>
          
          {/* SIDEBAR DIV */}
          <aside style={{display: "flex", flexDirection: "column", gap: "24px"}}>
            
            {/* PDF SECTION */}
            <section style={{border: "1px solid #262626", borderRadius: "8px", padding: "16px", backgroundColor: "#171717"}}>
              <h2 style={{fontSize: "14px", fontWeight: "500", marginBottom: "12px", color: "#d4d4d4"}}>1. Manual PDF</h2>
              <input
                ref={pdfRef1}
                type="file"
                accept="application/pdf"
                onChange={doUploadPDF}
                style={{display: "none"}}
                data-testid="pdf-input"
              />
              <button
                onClick={() => { pdfRef1.current.click() }}
                disabled={isUploading == true}
                style={{width: "100%", fontSize: "14px", padding: "8px 0", borderRadius: "6px", backgroundColor: "#10b981", color: "#171717", fontWeight: "500", cursor: "pointer", border: "none", opacity: isUploading ? 0.5 : 1}}
                data-testid="upload-pdf-btn"
              >
                {isUploading ? "Indexing..." : (pdf_file_name != "" ? "Replace PDF" : "Upload PDF")}
              </button>
              
              {/* show pdf status if it exists */}
              {pdf_file_name != "" ? (
                <div style={{marginTop: "12px", fontSize: "12px", color: "#a3a3a3"}} data-testid="pdf-status">
                  <div style={{whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis"}}>📄 {pdf_file_name}</div>
                  <div style={{marginTop: "4px"}}>Indexed {numChunks} chunks</div>
                </div>
              ) : null}
            </section>

            {/* IMAGE SECTION */}
            <section style={{border: "1px solid #262626", borderRadius: "8px", padding: "16px", backgroundColor: "#171717"}}>
              <h2 style={{fontSize: "14px", fontWeight: "500", marginBottom: "12px", color: "#d4d4d4"}}>2. Product Images</h2>
              <input
                ref={imgRef2}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                multiple={true}
                onChange={doUploadImages}
                style={{display: "none"}}
                data-testid="image-input"
              />
              <button
                onClick={() => { imgRef2.current.click() }}
                style={{width: "100%", fontSize: "14px", padding: "8px 0", borderRadius: "6px", border: "1px solid #404040", backgroundColor: "transparent", color: "white", cursor: "pointer"}}
                data-testid="upload-image-btn"
              >
                Add Images
              </button>
              
              {/* show images if they exist */}
              {myImages.length > 0 ? (
                <div style={{marginTop: "12px", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px"}} data-testid="image-list">
                  {myImages.map((imgg, index) => (
                    <div key={index} style={{position: "relative"}}>
                      <img src={imgg.url} style={{width: "100%", height: "64px", objectFit: "cover", borderRadius: "4px", border: "1px solid #262626"}} />
                      <button
                        onClick={() => { deleteImg(index) }}
                        style={{position: "absolute", top: "-4px", right: "-4px", width: "20px", height: "20px", borderRadius: "10px", backgroundColor: "#ef4444", color: "white", fontSize: "12px", border: "none", cursor: "pointer"}}
                        data-testid={`remove-image-${index}`}
                      >
                        x
                      </button>
                    </div>
                  ))}
                </div>
              ) : null}
            </section>

            {/* HOW IT WORKS SECTION */}
            <section style={{border: "1px solid #262626", borderRadius: "8px", padding: "16px", backgroundColor: "#171717", fontSize: "12px", color: "#a3a3a3"}}>
              <div style={{fontWeight: "500", color: "#d4d4d4", marginBottom: "8px"}}>How it works</div>
              <ol style={{paddingLeft: "16px", margin: "0", display: "flex", flexDirection: "column", gap: "4px"}}>
                <li>PDF text is chunked and embedded.</li>
                <li>Chunks are stored in a FAISS index.</li>
                <li>Your question retrieves top chunks.</li>
                <li>Gemini reads chunks + images and answers.</li>
              </ol>
            </section>
          </aside>

          {/* MAIN CHAT WINDOW */}
          <main style={{border: "1px solid #262626", borderRadius: "8px", backgroundColor: "#171717", display: "flex", flexDirection: "column", minHeight: "600px"}}>
            
            {/* messages area */}
            <div style={{flex: 1, overflowY: "auto", padding: "16px", display: "flex", flexDirection: "column", gap: "16px"}} data-testid="chat-window">
              {all_msgs.length == 0 ? (
                <div style={{textAlign: "center", color: "#737373", fontSize: "14px", marginTop: "80px"}}>
                  Ask a troubleshooting question to begin.
                </div>
              ) : null}
              
              {/* loop thru msgs */}
              {all_msgs.map((msgItem, idx) => (
                <div key={idx} style={{display: "flex", justifyContent: msgItem.role == "user" ? "flex-end" : "flex-start"}}>
                  <div
                    style={msgItem.role == "user" ? 
                      {maxWidth: "80%", backgroundColor: "#10b981", color: "#171717", borderRadius: "8px", padding: "12px"} : 
                      {maxWidth: "85%", backgroundColor: "#262626", color: "#f5f5f5", borderRadius: "8px", padding: "12px"}
                    }
                    data-testid={`msg-${idx}`}
                  >
                    
                    {/* user images */}
                    {msgItem.images && msgItem.images.length > 0 ? (
                      <div style={{display: "flex", gap: "8px", marginBottom: "8px"}}>
                        {msgItem.images.map((u, j) => (
                          <img key={j} src={u} style={{width: "64px", height: "64px", objectFit: "cover", borderRadius: "4px"}} />
                        ))}
                      </div>
                    ) : null}
                    
                    <div style={{whiteSpace: "pre-wrap", fontSize: "14px"}}>{msgItem.text}</div>
                    
                    {/* assistant context */}
                    {msgItem.context && msgItem.context.length > 0 ? (
                      <details style={{marginTop: "12px", fontSize: "12px"}}>
                        <summary style={{cursor: "pointer", color: "#a3a3a3"}}>
                          Sources ({msgItem.context.length})
                        </summary>
                        <div style={{marginTop: "8px", display: "flex", flexDirection: "column", gap: "8px"}}>
                          {msgItem.context.map((c_obj, k) => (
                            <div key={k} style={{backgroundColor: "#171717", border: "1px solid #404040", borderRadius: "4px", padding: "8px"}}>
                              <div style={{color: "#737373", marginBottom: "4px"}}>Chunk {k + 1} · score {c_obj.score.toFixed(3)}</div>
                              <div style={{color: "#d4d4d4"}}>{c_obj.text.slice(0, 300)}{c_obj.text.length > 300 ? "..." : ""}</div>
                            </div>
                          ))}
                        </div>
                      </details>
                    ) : null}
                  </div>
                </div>
              ))}
              
              {/* loading state */}
              {isThinking == true ? (
                <div style={{display: "flex", justifyContents: "flex-start"}} data-testid="loading">
                  <div style={{backgroundColor: "#262626", borderRadius: "8px", padding: "12px", fontSize: "14px", color: "#a3a3a3"}}>Thinking...</div>
                </div>
              ) : null}
            </div>

            {/* show error */}
            {errorMsg != "" ? (
              <div style={{margin: "0 16px 8px 16px", fontSize: "12px", color: "#f87171"}} data-testid="error-msg">{errorMsg}</div>
            ) : null}

            {/* input area at bottom */}
            <div style={{borderTop: "1px solid #262626", padding: "16px"}}>
              <div style={{display: "flex", gap: "8px"}}>
                <input
                  type="text"
                  value={q}
                  onChange={(e) => { setQ(e.target.value) }}
                  onKeyDown={(e) => { if (e.key == "Enter") doAsk() }}
                  placeholder="Describe the issue..."
                  style={{flex: 1, backgroundColor: "#0a0a0a", border: "1px solid #404040", borderRadius: "6px", padding: "8px 12px", fontSize: "14px", color: "white", outline: "none"}}
                  data-testid="question-input"
                />
                <button
                  onClick={doAsk}
                  disabled={isThinking == true || q.trim() == ""}
                  style={{padding: "8px 16px", borderRadius: "6px", backgroundColor: "#10b981", color: "#171717", fontWeight: "500", fontSize: "14px", border: "none", cursor: "pointer", opacity: (isThinking || q.trim() == "") ? 0.5 : 1}}
                  data-testid="ask-btn"
                >
                  {isThinking ? "..." : "Ask"}
                </button>
              </div>
            </div>
          </main>

        </div>
      </div>
    </div>
  );
}

export default App;
