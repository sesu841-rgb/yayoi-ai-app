const circle = document.querySelector('.progress-ring__circle');
const radius = circle.r.baseVal.value;
const circumference = radius * 2 * Math.PI;

circle.style.strokeDasharray = `${circumference} ${circumference}`;
circle.style.strokeDashoffset = 0; // Start full

function setProgress(percent) {
    const offset = circumference - (percent / 100) * circumference;
    circle.style.strokeDashoffset = offset;
}

const timeDisplay = document.getElementById('time-display');
const startBtn = document.getElementById('start-btn');
const resetBtn = document.getElementById('reset-btn');
const minutesInput = document.getElementById('minutes-input');

let timerInterval;
let totalTime = 25 * 60;
let timeLeft = totalTime;
let isRunning = false;

// Audio Context for sound
let audioCtx;

function initAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
}

function playRelaxingSound() {
    initAudio();
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    // Create a bell-like sound
    // Fundamental frequency
    oscillator.type = 'sine'; // deeply relaxing sine wave
    oscillator.frequency.setValueAtTime(528, audioCtx.currentTime); // 528Hz Solfeggio frequency (believed to be healing/relaxing)

    // Envelope
    const now = audioCtx.currentTime;
    gainNode.gain.setValueAtTime(0, now);
    gainNode.gain.linearRampToValueAtTime(0.3, now + 0.1); // Attack
    gainNode.gain.exponentialRampToValueAtTime(0.001, now + 4); // Long decay

    oscillator.start(now);
    oscillator.stop(now + 4);

    // Add a second harmonic for richness (lower volume)
    const osc2 = audioCtx.createOscillator();
    const gain2 = audioCtx.createGain();
    osc2.connect(gain2);
    gain2.connect(audioCtx.destination);
    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(528 * 2, now); // Octave up
    
    gain2.gain.setValueAtTime(0, now);
    gain2.gain.linearRampToValueAtTime(0.1, now + 0.1);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 3);

    osc2.start(now);
    osc2.stop(now + 3);
}

function updateDisplay() {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    timeDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    // Update progress ring (inverse logic: empty as time goes down)
    // We want the ring to shrink as time passes.
    // Progress starts at 100% (full ring) and goes to 0% (empty ring)
    const percentage = (timeLeft / totalTime) * 100;
    // However, setProgress calculates offset.
    // If percent is 100, offset is 0 (full ring).
    // If percent is 0, offset is circumference (empty ring).
    setProgress(percentage);
}

function startTimer() {
    if (isRunning) {
        // Pause logic
        clearInterval(timerInterval);
        startBtn.textContent = 'Start';
        isRunning = false;
        return;
    }

    // Start logic
    initAudio(); // Initialize audio context on user interaction
    startBtn.textContent = 'Pause';
    isRunning = true;
    
    // If starting fresh or after reset
    if (timeLeft === undefined || timeLeft <= 0) {
       totalTime = parseInt(minutesInput.value) * 60;
       timeLeft = totalTime;
    }

    timerInterval = setInterval(() => {
        timeLeft--;
        updateDisplay();

        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            isRunning = false;
            startBtn.textContent = 'Start';
            timeLeft = 0;
            updateDisplay();
            playRelaxingSound();
        }
    }, 1000);
}

function resetTimer() {
    clearInterval(timerInterval);
    isRunning = false;
    startBtn.textContent = 'Start';
    totalTime = parseInt(minutesInput.value) * 60;
    timeLeft = totalTime;
    updateDisplay();
    // Reset ring to full
    setProgress(100); 
}

startBtn.addEventListener('click', startTimer);
resetBtn.addEventListener('click', resetTimer);

minutesInput.addEventListener('change', () => {
    if (!isRunning) {
        totalTime = parseInt(minutesInput.value) * 60;
        timeLeft = totalTime;
        updateDisplay();
        setProgress(100);
    }
});

// Initial setup
updateDisplay();
setProgress(100);
