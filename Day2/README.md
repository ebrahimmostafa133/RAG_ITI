# 🏥 Multi-Modal Medical AI Agent

A comprehensive medical AI assistant with both Jupyter notebook and modern web interface capabilities.

## 🚀 Quick Start

### Web Interface (Recommended)
```bash
# Run the web application
./run_web_app.sh
# Or manually: streamlit run app.py
```

### Jupyter Notebook
```bash
jupyter notebook medical_agent.ipynb
```

## Features

- **💬 Interactive Chat Interface**: Natural conversation with the medical AI agent
- **🖼️ Multi-Modal Input**: Support for text symptoms and image uploads (MRI/CT scans)
- **🏥 Hospital Search**: Find nearby hospitals by specialty and location
- **📋 Case Management**: Store and view patient cases in CSV format
- **🔒 Secure**: Environment-based API key management
- **⚠️ Safe**: Built-in medical disclaimers and safety measures

## Setup

### 1. Environment Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. API Key Configuration

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Run the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## Usage

### Basic Case Analysis

1. **Enter Symptoms**: Describe patient symptoms in the text area
2. **Upload Images** (Optional): Upload MRI/CT scan images
3. **Click "Analyze Case"**: Get AI-powered analysis and insights

### Hospital Search

- Use the "🏥 Find Hospitals" quick action button
- Or type queries like "Find cardiology hospitals in Cairo"

### Case Storage

- Use "💾 Save Current Case" to store analyzed cases
- View stored cases in the sidebar
- Download cases as CSV file

### Quick Actions

- **🏥 Find Hospitals**: Search for medical facilities
- **💾 Save Current Case**: Store case data
- **📋 View Recent Cases**: See latest stored cases

## Interface Preview

### Main Dashboard
- **Header**: Medical AI Assistant branding with disclaimer
- **Chat Area**: Real-time conversation with color-coded messages
- **Input Section**: Text description + image upload
- **Quick Actions**: Hospital search, case saving, case viewing

### Sidebar Features
- **Case Database**: View stored patient cases
- **CSV Export**: Download case data
- **Session Management**: Clear conversation history

### Sample Interaction
```
User: Patient has severe headache, nausea, and sensitivity to light. MRI shows increased signal in temporal lobe.

Agent: ### Case Summary for [Patient]
**Symptoms:** Severe headache, nausea, sensitivity to light
**MRI Findings:** Increased signal in temporal lobe

#### Analysis:
- **Possible Conditions:** Migraine, meningitis, or other neurological conditions
- **Recommendations:** Seek immediate medical attention

⚠️ This is not a medical diagnosis. Consult a doctor.
```

## Usage Examples

### 1. Symptom Analysis
```
Input: "Patient reports chest pain, shortness of breath. CT scan shows pulmonary embolism."
Output: Structured analysis with insights and recommendations
```

### 2. Hospital Search
```
Input: "Find cardiology hospitals in New York"
Output: Hospital list with addresses and contact information
```

### 3. Case Storage
```
Input: "Save this case for John Doe"
Output: Case stored in CSV with timestamp
```

## Safety & Disclaimers

⚠️ **IMPORTANT MEDICAL DISCLAIMER**:
- This application provides general medical information only
- **NOT a substitute for professional medical advice**
- Always consult qualified healthcare professionals
- Never use for emergency medical situations

## Technical Details

### Architecture
- **Frontend**: Streamlit web interface
- **Backend**: LangGraph agent workflow
- **AI Model**: GPT-4o-mini with vision capabilities
- **Tools**: Hospital search, case storage
- **Storage**: CSV-based case management

### Dependencies
- `streamlit`: Web interface framework
- `langchain-openai`: OpenAI integration
- `langgraph`: Agent workflow management
- `pandas`: Data processing
- `Pillow`: Image processing

### Security
- API keys stored in environment variables
- Sensitive files excluded from version control
- Input validation and sanitization

## File Structure

```
medical_agent/
├── app.py                 # Streamlit web application
├── medical_agent.py       # Core agent logic and tools
├── medical_agent.ipynb    # Original Jupyter notebook
├── run_web_app.sh         # Web app launcher script
├── requirements.txt       # Python dependencies
├── README.md              # This documentation
├── .env.example          # Environment variables template
├── .env                  # Your API keys (not in git)
├── .gitignore           # Excluded files
└── patient_cases.csv    # Stored case data
```

## Troubleshooting

### Common Issues

1. **"API key not found"**
   - Ensure `.env` file exists with `OPENAI_API_KEY=your_key`

2. **"Module not found"**
   - Run `pip install -r requirements.txt`

3. **Application won't start**
   - Check if port 8501 is available
   - Try `streamlit run app.py --server.port 8502`

4. **Image upload issues**
   - Ensure images are JPG, PNG, or DICOM format
   - Check file size limits

### Performance Tips

- Keep conversations focused on single cases
- Use clear, descriptive symptom descriptions
- Upload high-quality medical images when possible

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and research purposes. Ensure compliance with medical data privacy regulations (HIPAA, GDPR, etc.) when deploying.

---

**Remember**: This tool is designed to assist healthcare professionals and should never replace human medical expertise. Always prioritize patient safety and consult qualified medical practitioners for diagnosis and treatment.
