import { useState } from "react";
import "./App.css";

function App() {
  // ==========================================
  // AI ASSISTANT STATE
  // ==========================================

  const [showAssistant, setShowAssistant] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // ==========================================
  // PRESCRIPTION STATE
  // ==========================================

  const [selectedFile, setSelectedFile] = useState(null);
  const [prescriptionResults, setPrescriptionResults] = useState([]);
  const [risks, setRisks] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  // ==========================================
  // AI ASSISTANT
  // ==========================================

  const askAI = async () => {
    const question = message.trim();

    if (!question || loading) {
      return;
    }

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text: question,
      },
    ]);

    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(
  "https://medguard-ai-backend.onrender.com/ask-ai",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question: question,
    }),
  }
);

      if (!response.ok) {
        throw new Error(
          `Server returned ${response.status}`
        );
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(
          data.answer || "AI request failed"
        );
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer,
        },
      ]);

    } catch (error) {
      console.error("MedGuard AI error:", error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text:
            "Sorry, I couldn't connect to MedGuard AI right now. Please make sure the backend is running.",
        },
      ]);

    } finally {
      setLoading(false);
    }
  };

  // ==========================================
  // AI SUGGESTIONS
  // ==========================================

  const useSuggestion = (question) => {
    setMessage(question);
  };

  // ==========================================
  // FILE SELECTION
  // ==========================================

  const handleFileChange = (event) => {
    const file = event.target.files[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);
    setPrescriptionResults([]);
    setRisks([]);
    setUploadMessage(
      "Prescription selected. Click Analyze Prescription."
    );
  };

  // ==========================================
  // ANALYZE PRESCRIPTION
  // ==========================================

  const analyzePrescription = async () => {
    if (!selectedFile) {
      setUploadMessage(
        "Please select a prescription image first."
      );
      return;
    }

    setAnalyzing(true);
    setPrescriptionResults([]);
    setRisks([]);
    setUploadMessage("Reading prescription...");

    try {
      const formData = new FormData();

      formData.append(
        "file",
        selectedFile
      );

      const response = await fetch(
        "https://medguard-ai-backend.onrender.com/analyze-prescription",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(
          `Server returned ${response.status}`
        );
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(
          "Prescription analysis failed."
        );
      }

      setPrescriptionResults(
        data.results || []
      );

      setRisks(
        data.risks || []
      );

      if (
        data.results &&
        data.results.length > 0
      ) {
        setUploadMessage(
          "Prescription analyzed successfully."
        );
      } else {
        setUploadMessage(
          "No medicines could be confidently identified."
        );
      }

    } catch (error) {
      console.error(
        "Prescription analysis error:",
        error
      );

      setUploadMessage(
        "Could not analyze the prescription. Please make sure the backend is running."
      );

    } finally {
      setAnalyzing(false);
    }
  };

  // ==========================================
  // OPEN FILE PICKER
  // ==========================================

  const openFilePicker = () => {
    document
      .getElementById("prescription-file")
      ?.click();
  };

  return (
    <div className="medguard-app">

      {/* ===================================== */}
      {/* NAVBAR */}
      {/* ===================================== */}

      <nav className="navbar">

        <div className="brand">
          <span className="brand-icon">
            💊
          </span>

          <span>
            MedGuard
          </span>
        </div>

        <div className="nav-links">

          <a href="#home">
            Home
          </a>

          <a href="#prescription">
            Prescription
          </a>

          <a href="#features">
            Features
          </a>

          <a href="#assistant">
            AI Assistant
          </a>

        </div>

      </nav>


      {/* ===================================== */}
      {/* HERO */}
      {/* ===================================== */}

      <main id="home">

        <section className="hero">

          <div className="hero-badge">
            AI-POWERED MEDICINE ASSISTANT
          </div>

          <h1>
            Understand your
            <br />
            <span>
              prescription.
            </span>
          </h1>

          <p className="hero-description">
            MedGuard helps you understand medicines,
            check prescriptions, and access medication
            information with the help of AI.
          </p>

          <div className="hero-buttons">

            <button
              className="primary-button"
              onClick={() =>
                document
                  .getElementById(
                    "prescription"
                  )
                  ?.scrollIntoView({
                    behavior: "smooth",
                  })
              }
            >
              📸 Analyze Prescription
            </button>

            <button
              className="secondary-button"
              onClick={() =>
                setShowAssistant(true)
              }
            >
              🤖 Ask MedGuard AI
            </button>

          </div>

        </section>


        {/* ===================================== */}
        {/* PRESCRIPTION ANALYZER */}
        {/* ===================================== */}

        <section
          id="prescription"
          className="features-section"
        >

          <div className="section-label">
            PRESCRIPTION ANALYZER
          </div>

          <h2>
            Upload your prescription.
            <br />
            Let MedGuard read it.
          </h2>

          <div className="prescription-card">

            <div className="upload-icon">
              📸
            </div>

            <h3>
              Upload Prescription
            </h3>

            <p>
              Upload a clear photo of your
              prescription. MedGuard will use OCR,
              AI and its medicine database to
              identify medicines.
            </p>

            <input
              id="prescription-file"
              type="file"
              accept=".png,.jpg,.jpeg"
              onChange={handleFileChange}
              style={{
                display: "none",
              }}
            />

            <button
              className="secondary-button"
              onClick={openFilePicker}
            >
              Choose Prescription
            </button>

            {selectedFile && (

              <div className="selected-file">

                <span>
                  📄 {selectedFile.name}
                </span>

                <button
                  className="primary-button"
                  onClick={analyzePrescription}
                  disabled={analyzing}
                >
                  {analyzing
                    ? "Analyzing..."
                    : "Analyze Prescription"}
                </button>

              </div>

            )}

            {uploadMessage && (

              <p className="upload-status">
                {uploadMessage}
              </p>

            )}

          </div>


          {/* ================================= */}
          {/* PRESCRIPTION RESULTS */}
          {/* ================================= */}

          {prescriptionResults.length > 0 && (

            <div className="prescription-results">

              <div className="section-label">
                ANALYSIS RESULTS
              </div>

              <h3>
                Medicines detected
              </h3>

              {prescriptionResults.map(
                (result, index) => (

                  <div
                    className="medicine-result"
                    key={index}
                  >

                    <div className="medicine-result-icon">
                      💊
                    </div>

                    <div className="medicine-result-info">

                      <strong>
                        {result.ocr_name}
                      </strong>

                      <span>
                        Form:{" "}
                        {result.form || "Unknown"}
                      </span>

                      {result.dosage && (
                        <span>
                          Dosage:{" "}
                          {result.dosage}
                        </span>
                      )}

                    </div>

                    <div className="medicine-match">

                      {result.verified ? (

                        <>
                          <span className="match-success">
                            ✓ Matched
                          </span>

                          <strong>
                            {result.match}
                          </strong>

                          <small>
                            Confidence:{" "}
                            {result.confidence.toFixed(
                              1
                            )}
                            %
                          </small>
                        </>

                      ) : (

                        <>
                          <span className="match-warning">
                            ⚠ Uncertain
                          </span>

                          <small>
                            Confidence:{" "}
                            {result.confidence.toFixed(
                              1
                            )}
                            %
                          </small>

                        </>
                      )}

                    </div>

                  </div>

                )
              )}

            </div>

          )}


          {/* ================================= */}
          {/* SAFETY RESULTS */}
          {/* ================================= */}

          {prescriptionResults.length > 0 && (

            <div className="safety-box">

              <h3>
                🛡️ Safety Check
              </h3>

              {risks.length > 0 ? (

                risks.map(
                  (risk, index) => (

                    <div
                      className="risk-item"
                      key={index}
                    >
                      🚨
                      <span>
                        <strong>
                          Duplicate ingredient:
                        </strong>{" "}
                        {risk.ingredient}
                        {" "}appears in{" "}
                        {risk.medicines.join(
                          " and "
                        )}
                      </span>
                    </div>

                  )
                )

              ) : (

                <p>
                  ✅ No overlapping ingredient
                  risks found among confidently
                  matched medicines.
                </p>

              )}

            </div>

          )}

        </section>


        {/* ===================================== */}
        {/* FEATURES */}
        {/* ===================================== */}

        <section
          id="features"
          className="features-section"
        >

          <div className="section-label">
            WHAT MEDGUARD DOES
          </div>

          <h2>
            One place for
            <br />
            your medicine information.
          </h2>

          <div className="feature-grid">

            <div className="feature-card">

              <div className="feature-icon">
                📸
              </div>

              <h3>
                Prescription Reading
              </h3>

              <p>
                Upload a prescription and MedGuard
                uses OCR and AI-assisted processing
                to extract medicine information.
              </p>

            </div>


            <div className="feature-card">

              <div className="feature-icon">
                🔍
              </div>

              <h3>
                Medicine Database
              </h3>

              <p>
                Search MedGuard's medicine database
                to find information about medicines
                and their compositions.
              </p>

            </div>


            <div className="feature-card">

              <div className="feature-icon">
                🤖
              </div>

              <h3>
                AI Assistant
              </h3>

              <p>
                Ask MedGuard AI questions about
                medicines and prescriptions using
                Gemini.
              </p>

              <button
                className="card-button"
                onClick={() =>
                  setShowAssistant(true)
                }
              >
                Open AI Assistant →
              </button>

            </div>

          </div>

        </section>


        {/* ===================================== */}
        {/* AI ASSISTANT SECTION */}
        {/* ===================================== */}

        <section
          id="assistant"
          className="assistant-section"
        >

          <div className="assistant-icon">
            🤖
          </div>

          <div className="section-label">
            MEDGUARD AI
          </div>

          <h2>
            Your medicine
            <br />
            questions, answered.
          </h2>

          <p>
            Ask MedGuard AI about medicines,
            prescriptions, and general medication
            information.
          </p>

          <button
            className="primary-button"
            onClick={() =>
              setShowAssistant(true)
            }
          >
            🤖 Open MedGuard AI
          </button>

        </section>

      </main>


      {/* ===================================== */}
      {/* FOOTER */}
      {/* ===================================== */}

      <footer>

        <div className="footer-brand">
          💊 MedGuard
        </div>

        <p>
          AI-assisted prescription understanding.
        </p>

        <small>
          MedGuard does not replace professional
          medical advice or pharmacist verification.
        </small>

      </footer>


      {/* ===================================== */}
      {/* AI CHAT POPUP */}
      {/* ===================================== */}

      {showAssistant && (

        <div className="ai-overlay">

          <div className="ai-chat-window">

            <div className="ai-header">

              <div className="ai-header-left">

                <div className="ai-avatar">
                  🤖
                </div>

                <div>

                  <h3>
                    MedGuard AI
                  </h3>

                  <span>
                    ● Online
                  </span>

                </div>

              </div>

              <button
                className="close-button"
                onClick={() =>
                  setShowAssistant(false)
                }
              >
                ✕
              </button>

            </div>


            <div className="ai-chat-body">

              {messages.length === 0 && (

                <div className="ai-welcome">

                  <div className="welcome-icon">
                    💊
                  </div>

                  <h3>
                    Hi! I'm MedGuard AI
                  </h3>

                  <p>
                    Ask me about medicines,
                    prescriptions, or general
                    medication information.
                  </p>

                  <div className="suggestions">

                    <button
                      onClick={() =>
                        useSuggestion(
                          "What is paracetamol?"
                        )
                      }
                    >
                      💊 What is paracetamol?
                    </button>

                    <button
                      onClick={() =>
                        useSuggestion(
                          "What information can you give me about a medicine?"
                        )
                      }
                    >
                      🔎 Medicine information
                    </button>

                    <button
                      onClick={() =>
                        useSuggestion(
                          "How can I understand a prescription?"
                        )
                      }
                    >
                      📋 Prescription help
                    </button>

                  </div>

                </div>

              )}


              {messages.map(
                (msg, index) => (

                  <div
                    key={index}
                    className={
                      msg.role === "user"
                        ? "chat-row user-row"
                        : "chat-row ai-row"
                    }
                  >

                    <div className="message-avatar">
                      {msg.role === "user"
                        ? "👤"
                        : "🤖"}
                    </div>

                    <div className="message-bubble">
                      {msg.text}
                    </div>

                  </div>

                )
              )}


              {loading && (

                <div className="chat-row ai-row">

                  <div className="message-avatar">
                    🤖
                  </div>

                  <div className="message-bubble typing">
                    MedGuard AI is thinking...
                  </div>

                </div>

              )}

            </div>


            <div className="ai-input-area">

              <input
                type="text"
                value={message}
                placeholder="Ask MedGuard something..."
                onChange={(e) =>
                  setMessage(e.target.value)
                }
                onKeyDown={(e) => {

                  if (
                    e.key === "Enter" &&
                    !e.shiftKey
                  ) {
                    e.preventDefault();
                    askAI();
                  }

                }}
              />

              <button
                className="send-button"
                onClick={askAI}
                disabled={
                  loading ||
                  !message.trim()
                }
              >
                ➤
              </button>

            </div>


            <div className="ai-disclaimer">

              MedGuard AI provides general
              information and does not replace
              professional medical advice.

            </div>

          </div>

        </div>

      )}

    </div>
  );
}

export default App;