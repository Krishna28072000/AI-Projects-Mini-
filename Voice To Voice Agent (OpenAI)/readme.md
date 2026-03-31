# 🎤 Voice-to-Voice AI Assistant (OpenAI Agents SDK)

## 🚀 Overview

This project implements a **Voice-to-Voice AI Assistant** that allows users to interact with an AI system using natural speech.

The assistant:

* 🎤 Takes input from the microphone
* 🧠 Processes it using an AI agent
* 🔊 Responds back using generated speech

It is built using:

* OpenAI Agents SDK (Voice Pipeline)
* Python (CLI + Notebook compatible)
* Real-time audio processing

---

## ✨ Features

* Real-time **speech-to-speech interaction**
* AI-powered responses using **OpenAI models**
* Works in both:

  * 🖥️ Python CLI (`.py`)
  * 📓 Jupyter Notebook
* Customizable **voice personality & tone**
* Continuous conversation loop

---

## 📦 Requirements

Install dependencies:

```bash
pip install numpy sounddevice python-dotenv openai-agents[voice]
```

---

## 🔑 Setup

### 1. Set API Key

#### Windows (Command Prompt)

```bash
set OPENAI_API_KEY=your_api_key_here
```

#### Or use `.env` file

```env
OPENAI_API_KEY=your_api_key_here
```

---

## ▶️ Running the Project

### 🖥️ Run as Python Script

```bash
python voice_agent.py
```

### 📓 Run in Jupyter Notebook

* Run cells step-by-step
* Ensure microphone access is enabled
* Use async execution:

```python
await voice_assistant_loop(pipeline, input_device)
```

---

## 🎯 How It Works

### 🔄 Workflow

```
User Voice 🎤
   ↓
Audio Recording (sounddevice)
   ↓
AudioInput (OpenAI Agents)
   ↓
AI Processing (Agent)
   ↓
Text Response
   ↓
Speech Generation (TTS)
   ↓
Audio Output 🔊
```

---

## 🧠 Core Components

### 🔹 Agent

* Defines AI behavior
* Uses instructions to guide responses

### 🔹 Voice Pipeline

* Handles:

  * Speech → Text
  * AI → Response
  * Text → Speech

### 🔹 Audio Processing

* Captures real-time microphone input
* Streams output to speakers

---

## ⚙️ Usage Instructions

1. Run the script
2. Press **Enter** to start recording
3. Speak your query
4. Press **Enter** again to stop
5. Listen to AI response
6. Type `q` to exit

---

## 📁 Project Structure

```
voice-assistant/
│── voice_agent.py        # Main CLI script
│── notebook.ipynb        # Optional notebook version
│── requirements.txt
│── README.md
```

---

## 🔊 Voice Customization

You can modify voice behavior in:

```python
TTSModelSettings(
    instructions="Your custom tone and personality"
)
```

---

## ⚠️ Notes

* Ensure microphone and speakers are working
* Requires internet connection
* Works best with a quiet environment

---

## 🔥 Future Improvements

* Add **wake word detection** (e.g., "Hey AI")
* Real-time streaming (no manual stop)
* GUI / Web app integration
* Multi-agent conversations
* Noise reduction & speech enhancement

---

## 👨‍💻 Author

**Krishna Chaitanya (KC)**

* 💼 1+ year experience at Quadone Technologies
* 🤖 Aspiring Generative AI Specialist
* 📫 [gkrishnac20000@gmail.com](mailto:gkrishnac20000@gmail.com)

---

## ⭐ Contribution

Feel free to fork, improve, and contribute!

---

## 📜 License

This project is open-source and free to use.
