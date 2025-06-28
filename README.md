# Smart Agentic Web App

A modern web application for uploading, processing, and analyzing CSV/XLS files with intelligent data visualization capabilities.

## 🚀 Features

- **File Upload**: Support for CSV and Excel files
- **Data Processing**: Automatic data cleaning and validation
- **Interactive Tables**: Display processed data in styled tables
- **Command Interface**: Natural language commands for data analysis
- **Data Visualization**: Generate plots and heatmaps using matplotlib
- **Modern UI**: Beautiful, responsive design with gradient backgrounds

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## 🛠️ Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd Smart-Agentic-web-app/Backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Start the backend server:
```bash
uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd Smart-Agentic-web-app/Frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (or next available port)

## 🎯 Usage

### 1. Upload Files
- Click "Select Files" to choose CSV or Excel files
- Supported formats: `.csv`, `.xls`, `.xlsx`
- Multiple files can be uploaded simultaneously

### 2. View Data
- After upload, data is automatically cleaned and displayed
- View summary statistics and data preview
- Check for any processing errors

### 3. Run Commands
Use natural language commands to analyze your data:

#### Basic Commands
- `show 10 rows` - Display first 10 rows
- `get 5` - Display first 5 rows
- `columns` - Show column information
- `shape` - Display data dimensions

#### Visualization Commands
- `plot top 10 <ColumnName>` - Create bar chart of top 10 values
- `heatmap <Column1> <Column2>` - Create heatmap between two columns

### 4. View Plots
- Plots are generated server-side using matplotlib
- Displayed as high-quality PNG images
- Responsive design adapts to different screen sizes

## 🏗️ Project Structure

```
Smart-Agentic-web-app/
├── Backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── README.md
├── Frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── UploadZone.vue  # Main upload component
│   │   ├── App.vue             # Root component
│   │   └── main.js             # Vue app entry point
│   ├── package.json            # Node.js dependencies
│   └── vite.config.js          # Vite configuration
└── README.md                   # This file
```

## 🔧 Technologies Used

### Backend
- **FastAPI**: Modern Python web framework
- **Pandas**: Data manipulation and analysis
- **Matplotlib**: Data visualization and plotting
- **Uvicorn**: ASGI server

### Frontend
- **Vue 3**: Progressive JavaScript framework
- **Vite**: Fast build tool and dev server
- **CSS3**: Modern styling with gradients and animations

## 📊 API Endpoints

### POST `/upload`
Upload and process CSV/Excel files
- **Input**: Multipart form data with files
- **Output**: Processing results with data preview

### POST `/command`
Execute data analysis commands
- **Input**: JSON with command and data
- **Output**: Command results or plot images

### GET `/health`
Health check endpoint
- **Output**: API status information

## 🎨 Features in Detail

### Data Processing
- Automatic CSV delimiter detection
- Data cleaning (remove empty rows/columns)
- Column name sanitization
- Multiple file support with concatenation

### Visualization
- **Bar Charts**: For frequency analysis
- **Heatmaps**: For correlation analysis
- **High Resolution**: 300 DPI output
- **Responsive**: Adapts to container size

### User Experience
- Drag-and-drop file upload
- Real-time progress feedback
- Error handling and validation
- Modern, intuitive interface

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   - Frontend will automatically try next available port
   - Check terminal output for actual port number

2. **CORS Errors**
   - Ensure backend is running on `http://localhost:8000`
   - Frontend should be on `http://localhost:5173`

3. **File Upload Issues**
   - Check file format (CSV/Excel only)
   - Ensure file is not corrupted
   - Verify file size is reasonable

4. **Plot Generation Errors**
   - Ensure matplotlib is properly installed
   - Check column names exist in data
   - Verify data types are compatible

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Built with Vue 3 and FastAPI
- Data visualization powered by Matplotlib
- Modern UI design with CSS gradients
- File processing with Pandas

---

**Happy Data Analysis! 📊✨** 