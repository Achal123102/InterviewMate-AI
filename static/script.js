document.addEventListener("DOMContentLoaded", () => {
  const cfg = window.aiInterview;
  const questionText = document.getElementById("q-text");
  if (!cfg || !questionText) return;

  const questions = cfg.questions || [];
  const responses = questions.map(() => ({ selected_index: null, answer: "" }));
  let current = 0;
  const mode = cfg.answerMode;

  // DOM Elements
  const mcqOptions = document.getElementById("mcq-options");
  const writtenArea = document.getElementById("written-area");
  const answerText = document.getElementById("answer-text");
  const nextBtn = document.getElementById("next-btn");
  const prevBtn = document.getElementById("prev-btn");
  const position = document.getElementById("q-position");
  const progress = document.getElementById("progress-fill");
  const answerCount = document.getElementById("answered-count");
  const voiceNote = document.getElementById("voice-note");
  const miniRows = Array.from(document.querySelectorAll("#mini-list > .mini-item"));
  const qBadge = document.getElementById("q-badge");
  const hintBox = document.getElementById("hint-box");
  const hintText = document.getElementById("hint-text");

  // Voice Agent DOM Elements
  const agentOrb = document.getElementById("agent-orb");
  const agentWave = document.getElementById("agent-wave");
  const agentStatusPill = document.getElementById("agent-status-pill");
  const agentCaption = document.getElementById("agent-caption");
  const agentRepeatBtn = document.getElementById("agent-repeat-btn");
  const agentHintBtn = document.getElementById("agent-hint-btn");
  const agentStopBtn = document.getElementById("agent-stop-btn");
  const autoSpeakChk = document.getElementById("auto-speak-chk");
  const voiceSelect = document.getElementById("voice-select");
  const voiceSpeed = document.getElementById("voice-speed");

  // Mic & Metrics Elements
  const speakBtn = document.getElementById("speak-answer");
  const micIcon = document.getElementById("mic-icon");
  const micText = document.getElementById("mic-text");
  const micLiveWave = document.getElementById("mic-live-wave");
  const micStatusLabel = document.getElementById("mic-status-label");
  const wordCountEl = document.getElementById("word-count");
  const speechPaceEl = document.getElementById("speech-pace");
  const fillerCountEl = document.getElementById("filler-count");
  const clearBtn = document.getElementById("clear-answer-btn");
  const addPeriodBtn = document.getElementById("add-period-btn");

  // Timers
  const qTimerEl = document.getElementById("q-timer");
  const totalTimerEl = document.getElementById("total-timer");
  let questionStartTime = Date.now();
  let sessionStartTime = Date.now();
  let timerInterval = null;

  // State
  let isListening = false;
  let recognition = null;
  let currentUtterance = null;
  let availableVoices = [];

  // =========================================================================
  // Timers
  // =========================================================================
  function formatTime(seconds) {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  }

  function startTimers() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      const qSec = Math.floor((Date.now() - questionStartTime) / 1000);
      const totSec = Math.floor((Date.now() - sessionStartTime) / 1000);
      if (qTimerEl) qTimerEl.textContent = formatTime(qSec);
      if (totalTimerEl) totalTimerEl.textContent = formatTime(totSec);
      updateSpeechPace(qSec);
    }, 1000);
  }

  // =========================================================================
  // Speech Metrics & Filler Word Detection
  // =========================================================================
  const FILLER_WORDS = ["um", "uh", "er", "ah", "like", "basically", "actually", "literally", "sort of", "kind of", "you know"];

  function updateAnswerMetrics() {
    const text = (answerText ? answerText.value : "").trim();
    const words = text ? text.split(/\s+/).filter(Boolean) : [];
    const count = words.length;

    if (wordCountEl) wordCountEl.textContent = `${count} word${count === 1 ? "" : "s"}`;

    // Count filler words
    let fillersFound = 0;
    const lower = text.toLowerCase();
    FILLER_WORDS.forEach(fw => {
      const regex = new RegExp(`\\b${fw}\\b`, "gi");
      const matches = lower.match(regex);
      if (matches) fillersFound += matches.length;
    });

    if (fillerCountEl) {
      fillerCountEl.textContent = `${fillersFound} filler${fillersFound === 1 ? "" : "s"} detected`;
      fillerCountEl.classList.toggle("warning", fillersFound > 2);
    }
  }

  function updateSpeechPace(qSec) {
    if (!speechPaceEl) return;
    const text = (answerText ? answerText.value : "").trim();
    const words = text ? text.split(/\s+/).filter(Boolean).length : 0;
    if (qSec > 5 && words > 0) {
      const wpm = Math.round((words / qSec) * 60);
      speechPaceEl.textContent = `${wpm} WPM`;
    } else {
      speechPaceEl.textContent = "0 WPM";
    }
  }

  // =========================================================================
  // Speech Synthesis (AI Voice Agent)
  // =========================================================================
  function loadVoices() {
    if (!("speechSynthesis" in window)) return;
    availableVoices = speechSynthesis.getVoices().filter(v => v.lang.startsWith("en"));
    if (voiceSelect) {
      voiceSelect.innerHTML = "";
      if (availableVoices.length === 0) {
        const opt = document.createElement("option");
        opt.textContent = "Default Browser Voice";
        voiceSelect.appendChild(opt);
      } else {
        availableVoices.forEach((v, i) => {
          const opt = document.createElement("option");
          opt.value = i;
          opt.textContent = `${v.name.replace(/Google|Microsoft/g, "").trim()} (${v.lang})`;
          if (v.name.includes("Female") || v.name.includes("Zira") || v.name.includes("Samantha") || v.name.includes("US English") || v.name.includes("Natural")) {
            opt.selected = true;
          }
          voiceSelect.appendChild(opt);
        });
      }
    }
  }

  if ("speechSynthesis" in window) {
    speechSynthesis.onvoiceschanged = loadVoices;
    loadVoices();
  }

  function setAgentState(state, captionText) {
    if (agentOrb) {
      agentOrb.className = `agent-orb ${state}`;
    }
    if (agentWave) {
      agentWave.classList.toggle("hidden", state !== "speaking");
    }
    if (agentStopBtn) {
      agentStopBtn.classList.toggle("hidden", state !== "speaking");
    }
    if (agentStatusPill) {
      if (state === "speaking") {
        agentStatusPill.textContent = "🔊 Speaking...";
        agentStatusPill.className = "agent-state-pill speaking";
      } else if (state === "listening") {
        agentStatusPill.textContent = "🎙 Listening to you...";
        agentStatusPill.className = "agent-state-pill listening";
      } else if (state === "hint") {
        agentStatusPill.textContent = "💡 Explaining Hint...";
        agentStatusPill.className = "agent-state-pill hint";
      } else {
        agentStatusPill.textContent = "Ready";
        agentStatusPill.className = "agent-state-pill ready";
      }
    }
    if (agentCaption && captionText) {
      agentCaption.textContent = captionText;
    }
  }

  function stopAgentSpeaking() {
    if ("speechSynthesis" in window) {
      speechSynthesis.cancel();
    }
    setAgentState("idle", "Ready for your answer.");
  }

  function speakQuestion(announce = true) {
    if (!("speechSynthesis" in window)) {
      if (voiceNote) voiceNote.textContent = "Text-to-speech is not supported in this browser.";
      return;
    }

    stopAgentSpeaking();
    if (isListening) stopListening();

    const q = questions[current];
    if (!q) return;

    let textToSpeak = "";
    const prefix = announce ? `Question ${current + 1} of ${questions.length}. ` : "";
    const badgeContext = q.badge ? `${q.badge}. ` : "";
    
    textToSpeak = `${prefix}${badgeContext}${q.question}`;

    if (mode === "MCQ" && q.options && q.options.length === 4) {
      const optLetters = ["A", "B", "C", "D"];
      const optsText = q.options.map((opt, i) => `Option ${optLetters[i]}: ${opt}`).join(". ");
      textToSpeak += `. Here are your choices: ${optsText}`;
    }

    currentUtterance = new SpeechSynthesisUtterance(textToSpeak);
    const speed = parseFloat(voiceSpeed ? voiceSpeed.value : 1.0) || 1.0;
    currentUtterance.rate = speed;
    currentUtterance.pitch = 1.0;

    if (availableVoices.length > 0 && voiceSelect) {
      const idx = parseInt(voiceSelect.value, 10);
      if (!isNaN(idx) && availableVoices[idx]) {
        currentUtterance.voice = availableVoices[idx];
      }
    }

    currentUtterance.onstart = () => {
      setAgentState("speaking", `Dr. Evelyn is reading Question ${current + 1}...`);
    };

    currentUtterance.onend = () => {
      setAgentState("idle", mode === "MCQ" ? "Select your choice or click 'Ask Aloud' to repeat." : "Ready! Speak your answer or type in the box.");
    };

    currentUtterance.onerror = () => {
      setAgentState("idle", "Ready for your answer.");
    };

    speechSynthesis.speak(currentUtterance);
  }

  function giveInterviewerHint() {
    const q = questions[current];
    if (!q) return;

    let hint = q.hint || "";
    if (!hint) {
      if (q.explanation && q.explanation.length > 10) {
        hint = `Consider the core principle: ${q.explanation.split(".")[0]}.`;
      } else if (mode === "MCQ") {
        hint = "Eliminate options that conflict with foundational programming standards or standard time complexity.";
      } else {
        hint = "Use the STAR method: define the Situation, your specific Task, the Action taken, and the measurable Result.";
      }
    }

    if (hintBox && hintText) {
      hintText.textContent = hint;
      hintBox.classList.remove("hidden");
    }

    if ("speechSynthesis" in window) {
      stopAgentSpeaking();
      const hintUtterance = new SpeechSynthesisUtterance(`Here is a hint from Dr. Evelyn: ${hint}`);
      hintUtterance.rate = parseFloat(voiceSpeed ? voiceSpeed.value : 1.0) || 1.0;
      hintUtterance.onstart = () => setAgentState("hint", `Dr. Evelyn: "${hint}"`);
      hintUtterance.onend = () => setAgentState("idle", "Take your time and deliver your best answer.");
      speechSynthesis.speak(hintUtterance);
    }
  }

  // =========================================================================
  // Speech Recognition (Candidate Voice Input)
  // =========================================================================
  function initRecognition() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) return null;

    const r = new Recognition();
    r.continuous = true;
    r.interimResults = true;
    r.lang = "en-US";

    r.onstart = () => {
      isListening = true;
      stopAgentSpeaking();
      setAgentState("listening", "Listening to your spoken answer...");
      if (micLiveWave) micLiveWave.classList.remove("hidden");
      if (micIcon) micIcon.textContent = "⏹";
      if (micText) micText.textContent = "Stop Recording";
      if (micStatusLabel) micStatusLabel.textContent = "Listening... Speak naturally.";
      if (speakBtn) {
        speakBtn.classList.remove("primary");
        speakBtn.classList.add("recording-active");
      }
    };

    r.onresult = (event) => {
      let finalTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript + " ";
        }
      }
      if (finalTranscript && answerText) {
        const cur = answerText.value.trim();
        answerText.value = cur ? `${cur} ${finalTranscript.trim()}` : finalTranscript.trim();
        responses[current].answer = answerText.value;
        if (answerCount) answerCount.textContent = `${countAnswered()} answered`;
        updateAnswerMetrics();
      }
    };

    r.onerror = (e) => {
      console.warn("Speech recognition error:", e.error);
      if (e.error !== "no-speech") {
        if (voiceNote) voiceNote.textContent = `Mic note: ${e.error}. You can also type.`;
      }
      stopListening();
    };

    r.onend = () => {
      stopListening();
    };

    return r;
  }

  function startListening() {
    stopAgentSpeaking();
    if (!recognition) recognition = initRecognition();
    if (!recognition) {
      if (voiceNote) voiceNote.textContent = "Speech recognition is not supported in this browser. Please type your response.";
      return;
    }
    try {
      recognition.start();
    } catch (_) {
      // already started
    }
  }

  function stopListening() {
    isListening = false;
    if (recognition) {
      try { recognition.stop(); } catch (_) {}
    }
    if (micLiveWave) micLiveWave.classList.add("hidden");
    if (micIcon) micIcon.textContent = "🎙";
    if (micText) micText.textContent = "Start Voice Answer";
    if (speakBtn) {
      speakBtn.classList.remove("recording-active");
      speakBtn.classList.add("primary");
    }
    setAgentState("idle", "Voice input captured. Review or continue answering.");
    updateAnswerMetrics();
  }

  function toggleListening() {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }

  // =========================================================================
  // Question Rendering
  // =========================================================================
  function countAnswered() {
    return responses.filter(r => mode === "MCQ" ? r.selected_index !== null : r.answer.trim().length > 0).length;
  }

  function render() {
    const q = questions[current];
    if (!q) return;

    questionStartTime = Date.now();
    if (qTimerEl) qTimerEl.textContent = "00:00";

    position.textContent = `QUESTION ${current + 1} OF ${questions.length}`;
    questionText.textContent = q.question;
    progress.style.width = `${((current + 1) / questions.length) * 100}%`;
    prevBtn.disabled = current === 0;
    nextBtn.textContent = current === questions.length - 1 ? "Finish interview ✓" : "Next →";
    answerCount.textContent = `${countAnswered()} answered`;

    miniRows.forEach((row, i) => row.classList.toggle("active", i === current));

    // Badge
    if (qBadge) {
      const isResume = q.category === "resume" || (q.badge && q.badge.toLowerCase().includes("resume"));
      qBadge.textContent = (isResume ? "📄 " : "🎯 ") + (q.badge || (isResume ? "Resume-Based" : "Role-Based"));
      qBadge.className = "badge-tag " + (isResume ? "resume-tag" : "role-tag");
    }

    // Hint Reset
    if (hintBox) hintBox.classList.add("hidden");

    // Hint caption
    document.getElementById("q-hint").textContent = mode === "MCQ"
      ? "Select the correct option. Dr. Evelyn will explain the reasoning in your results review."
      : "Explain your thought process with technical depth and a concrete example.";

    if (mode === "MCQ") {
      mcqOptions.classList.remove("hidden");
      writtenArea.classList.add("hidden");
      mcqOptions.innerHTML = "";
      (q.options || []).forEach((option, i) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "mcq-option" + (responses[current].selected_index === i ? " selected" : "");
        const letter = document.createElement("span");
        letter.className = "option-letter";
        letter.textContent = String.fromCharCode(65 + i);
        const text = document.createElement("span");
        text.textContent = option;
        button.append(letter, text);
        button.addEventListener("click", () => {
          responses[current].selected_index = i;
          render();
        });
        mcqOptions.appendChild(button);
      });
    } else {
      mcqOptions.classList.add("hidden");
      writtenArea.classList.remove("hidden");
      answerText.value = responses[current].answer || "";
      updateAnswerMetrics();
    }

    // Auto-Ask with Dr. Evelyn
    if (autoSpeakChk && autoSpeakChk.checked) {
      setTimeout(() => {
        speakQuestion(true);
      }, 350);
    } else {
      setAgentState("idle", `Question ${current + 1} ready. Click 'Ask Aloud' to hear Dr. Evelyn read it.`);
    }
  }

  // =========================================================================
  // Event Listeners
  // =========================================================================
  if (answerText) {
    answerText.addEventListener("input", () => {
      responses[current].answer = answerText.value;
      answerCount.textContent = `${countAnswered()} answered`;
      updateAnswerMetrics();
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (answerText) {
        answerText.value = "";
        responses[current].answer = "";
        updateAnswerMetrics();
      }
    });
  }

  if (addPeriodBtn) {
    addPeriodBtn.addEventListener("click", () => {
      if (answerText) {
        const val = answerText.value.trim();
        if (val && !val.endsWith(".")) {
          answerText.value = `${val}. `;
          responses[current].answer = answerText.value;
          updateAnswerMetrics();
        }
      }
    });
  }

  if (agentRepeatBtn) {
    agentRepeatBtn.addEventListener("click", () => speakQuestion(false));
  }

const readQuestionBtn = document.getElementById("read-question");

if (readQuestionBtn) {
  readQuestionBtn.addEventListener("click", () => {
    speakQuestion(false);
  });
}

  if (agentHintBtn) {
    agentHintBtn.addEventListener("click", giveInterviewerHint);
  }

  if (agentStopBtn) {
    agentStopBtn.addEventListener("click", stopAgentSpeaking);
  }

  if (speakBtn) {
    speakBtn.addEventListener("click", toggleListening);
  }

  prevBtn.addEventListener("click", () => {
    stopAgentSpeaking();
    if (isListening) stopListening();
    if (current > 0) {
      current--;
      render();
    }
  });

  nextBtn.addEventListener("click", async () => {
    stopAgentSpeaking();
    if (isListening) stopListening();

    if (current < questions.length - 1) {
      current++;
      render();
      return;
    }

    // Submit
    nextBtn.disabled = true;
    nextBtn.textContent = "Saving with AI evaluation...";
    setAgentState("speaking", "Interview finished! Analyzing your answers with Dr. Evelyn...");

    try {
      const res = await fetch("/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate: cfg.candidate,
          role: cfg.role,
          interview_type: cfg.interviewType,
          difficulty: cfg.difficulty,
          answer_mode: cfg.answerMode,
          match_score: cfg.matchScore,
          questions,
          answers: responses
        })
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Could not save interview.");
      window.location.href = `/result/${data.id}`;
    } catch (err) {
      if (voiceNote) voiceNote.textContent = `Could not save results: ${err.message}. Please try again.`;
      nextBtn.disabled = false;
      nextBtn.textContent = "Try again";
      setAgentState("idle", "Error saving interview. Please click Try Again.");
    }
  });

  // Global Keyboard Shortcuts
  document.addEventListener("keydown", (e) => {
    // Alt+R: Repeat question
    if (e.altKey && (e.key === "r" || e.key === "R")) {
      e.preventDefault();
      speakQuestion(false);
    }
    // Alt+H: Get hint
    if (e.altKey && (e.key === "h" || e.key === "H")) {
      e.preventDefault();
      giveInterviewerHint();
    }
    // Alt+S: Toggle voice answering
    if (e.altKey && (e.key === "s" || e.key === "S")) {
      e.preventDefault();
      toggleListening();
    }
    // Alt+N: Next question
    if (e.altKey && (e.key === "n" || e.key === "N")) {
      e.preventDefault();
      nextBtn.click();
    }
  });

  // Start timers and initial render
  startTimers();
  render();
});

/* InterviewMate AI Chatbot */
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("chatbot-toggle");
  const panel = document.getElementById("chatbot-panel");
  const close = document.getElementById("chatbot-close");
  const form = document.getElementById("chatbot-form");
  const input = document.getElementById("chatbot-input");
  const messages = document.getElementById("chatbot-messages");

  if (!toggle || !panel || !close || !form || !input || !messages) {
    return;
  }

  toggle.addEventListener("click", () => {
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden")) input.focus();
  });

  close.addEventListener("click", () => {
    panel.classList.add("hidden");
  });

  function addMessage(text, type) {
    const message = document.createElement("div");
    message.className = type === "user" ? "user-message" : "bot-message";
    message.textContent = text;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
    return message;
  }

  function getDemoReply(message) {
    const text = message.toLowerCase();

    if (text.includes("resume")) {
      return "Upload your PDF or DOCX resume on the dashboard. Add a job description to see a keyword-match estimate.";
    }

    if (text.includes("mcq") || text.includes("question")) {
      return "Choose an interview type and select MCQ mode to practise multiple-choice questions.";
    }

    if (text.includes("voice") || text.includes("speak") || text.includes("mic")) {
      return "Choose Written / Voice mode. Allow microphone access to speak your answer. Use Read Question to hear the question aloud.";
    }

    if (text.includes("score") || text.includes("result") || text.includes("feedback")) {
      return "Finish your mock interview to view your score and answer feedback. Open Interview History to review saved sessions.";
    }

    if (text.includes("hello") || text.includes("hi ") || text === "hi") {
      return "Hello! I'm InterviewMate, your interview practice assistant. Ask me about resumes, MCQs, voice mode or interview results.";
    }

    if (text.includes("interview") || text.includes("practice")) {
      return "Select Technical, HR, Aptitude or Coding on the dashboard. Then choose your difficulty and answer mode to start practising.";
    }

    return "I can help with resume uploads, mock interviews, MCQs, voice mode and interview results. What would you like help with?";
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    const text = input.value.trim();
    if (!text) return;

    addMessage(text, "user");
    input.value = "";

    const reply = getDemoReply(text);
    addMessage(reply, "bot");
  });
});

