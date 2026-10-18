document.addEventListener("DOMContentLoaded", () => {
  const cfg = window.aiInterview;
  const questionText = document.getElementById("q-text");
  if (!cfg || !questionText) return;
  const questions = cfg.questions || [];
  const responses = questions.map(() => ({selected_index: null, answer: ""}));
  let current = 0;
  const mode = cfg.answerMode;
  const mcqOptions = document.getElementById("mcq-options");
  const writtenArea = document.getElementById("written-area");
  const answerText = document.getElementById("answer-text");
  const nextBtn = document.getElementById("next-btn");
  const prevBtn = document.getElementById("prev-btn");
  const position = document.getElementById("q-position");
  const progress = document.getElementById("progress-fill");
  const answerCount = document.getElementById("answered-count");
  // 10-minute interview timer
const timerEl = document.getElementById("interview-timer");
let secondsLeft = 10 * 60;

function updateTimer() {
  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;

  timerEl.textContent =
    `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")} left`;

  if (secondsLeft <= 60) {
    timerEl.style.color = "#d93025";
  }

  if (secondsLeft <= 0) {
    clearInterval(timerInterval);
    timerEl.textContent = "Time's up!";
    voiceNote.textContent =
      "10 minutes are over. Finish your interview to see your result.";
    return;
  }

  secondsLeft--;
}

updateTimer();
const timerInterval = setInterval(updateTimer, 1000);
  const miniRows = Array.from(document.querySelectorAll("#mini-list > div"));

  function countAnswered() {
    return responses.filter(r => mode === "MCQ" ? r.selected_index !== null : r.answer.trim().length > 0).length;
  }
  function render() {
    const q = questions[current];
    position.textContent = `QUESTION ${current + 1} OF ${questions.length}`;
    questionText.textContent = q.question;
    progress.style.width = `${(current + 1) / questions.length * 100}%`;
    prevBtn.disabled = current === 0;
    nextBtn.textContent = current === questions.length - 1 ? "Finish interview ✓" : "Next →";
    answerCount.textContent = `${countAnswered()} answered`;
    miniRows.forEach((row, i) => row.classList.toggle("active", i === current));
    document.getElementById("q-hint").textContent = mode === "MCQ"
      ? "Choose one answer. You will see the correct option and explanation after finishing."
      : "Answer in your own words. Give a clear explanation and a relevant example.";
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
    }
  }
  if (answerText) answerText.addEventListener("input", () => {
    responses[current].answer = answerText.value;
    answerCount.textContent = `${countAnswered()} answered`;
  });
  prevBtn.addEventListener("click", () => { if (current > 0) current--; render(); });
  nextBtn.addEventListener("click", async () => {
    if (current < questions.length - 1) { current++; render(); return; }
    nextBtn.disabled = true;
    nextBtn.textContent = "Saving...";
    try {
      const res = await fetch("/submit", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          candidate: cfg.candidate, role: cfg.role, interview_type: cfg.interviewType,
          difficulty: cfg.difficulty, answer_mode: cfg.answerMode, match_score: cfg.matchScore,
          questions, answers: responses
        })
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Could not save interview.");
      window.location.href = `/result/${data.id}`;
    } catch (err) {
      voiceNote.textContent = `Could not save results: ${err.message}. Please try again.`;
      nextBtn.disabled = false;
      nextBtn.textContent = "Try again";
    }
  });

  const readBtn = document.getElementById("read-question");
  if (readBtn) readBtn.addEventListener("click", () => {
    if (!("speechSynthesis" in window)) { voiceNote.textContent = "Read-aloud is not supported in this browser."; return; }
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(questions[current].question);
    utterance.lang = "en-IN";
    speechSynthesis.speak(utterance);
    voiceNote.textContent = "Reading the question aloud...";
  });
  const speakBtn = document.getElementById("speak-answer");
  if (speakBtn) speakBtn.addEventListener("click", () => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) { voiceNote.textContent = "Speech input is not supported in this browser. Type your answer instead."; return; }
    const recognition = new Recognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    voiceNote.textContent = "Listening... speak now.";
    recognition.onresult = (event) => {
      const words = event.results[0][0].transcript;
      answerText.value = `${answerText.value ? answerText.value + " " : ""}${words}`;
      responses[current].answer = answerText.value;
      answerCount.textContent = `${countAnswered()} answered`;
      voiceNote.textContent = "Speech added to your answer.";
    };
    recognition.onerror = () => { voiceNote.textContent = "Voice input failed. You can type your answer."; };
    try { recognition.start(); } catch (_) { voiceNote.textContent = "Voice input is already active or unavailable."; }
  });
  render();
});
