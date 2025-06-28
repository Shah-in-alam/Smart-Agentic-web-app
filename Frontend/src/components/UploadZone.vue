<template>
    <div class="upload-zone">
      <div class="container">
        <h1 class="title">📊 Smart Agentic Web App</h1>
        <p class="subtitle">Upload and process your CSV/XLS files</p>
  
        <section class="file-upload">
          <label class="file-label">
            📁 Upload CSV/XLS Files
          </label>
          <input ref="fileInput" type="file" multiple @change="handleFiles" :accept="allowedFileTypes" id="fileInput" style="display: none;" />
          <button @click="openFileDialog" class="main-btn">Select Files</button>
        </section>
  
        <section v-if="files.length > 0" class="file-list">
          <h3>Selected Files:</h3>
          <ul>
            <li v-for="(file, index) in files" :key="index">
              <strong>{{ file.name }}</strong> - {{ formatFileSize(file.size) }}
              <span v-if="!isValidFile(file)" class="error">❌ Invalid file type</span>
            </li>
          </ul>
        </section>
  
        <button @click="uploadFiles" :disabled="files.length === 0 || uploading || hasInvalidFiles" class="main-btn upload-btn">
          <span v-if="uploading">Uploading...</span>
          <span v-else>Upload Files</span>
        </button>
  
        <section v-if="uploadResult && !uploadResult.error" class="result-summary">
          <h3>Upload Result:</h3>
          <div class="result-grid">
            <div>Total files received: {{ uploadResult.total_files_received }}</div>
            <div>Files processed: {{ uploadResult.files_processed }}</div>
            <div>Errors: {{ uploadResult.errors?.length || 0 }}</div>
            <div>Total rows: {{ uploadResult.summary?.total_rows || 0 }}</div>
            <div>Total columns: {{ uploadResult.summary?.total_columns || 0 }}</div>
            <div>Memory usage: {{ uploadResult.summary?.memory_usage || 'N/A' }}</div>
          </div>
  
          <h4>Preview Table:</h4>
          <div class="table-wrapper">
            <table class="styled-table">
              <thead>
                <tr>
                  <th v-for="(col, i) in uploadResult.columns" :key="i">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in uploadResult.preview" :key="i">
                  <td v-for="col in uploadResult.columns" :key="col">{{ row[col] }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
  
        <section v-if="uploadResult?.preview?.length" class="command-box">
          <h3>Ask a Command</h3>
          <div class="command-input">
            <input type="text" v-model="userCommand" placeholder="e.g. show 10 rows or plot top 10 PasswordHash" @keyup.enter="sendCommand" />
            <button @click="sendCommand" class="main-btn">Run</button>
          </div>
        </section>
  
        <section v-if="commandResult" class="command-result">
          <h3>Command Result:</h3>
          <div v-if="commandResult?.result">
            <div class="table-wrapper">
              <table class="styled-table">
                <thead>
                  <tr>
                    <th v-for="(col, i) in Object.keys(commandResult.result[0] || {})" :key="i">{{ col }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in commandResult.result" :key="i">
                    <td v-for="(val, j) in Object.values(row)" :key="j">{{ val }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div v-else-if="commandResult?.summary">
            <ul>
              <li><strong>Shape:</strong> {{ commandResult.summary.shape[0] }} rows x {{ commandResult.summary.shape[1] }} cols</li>
              <li><strong>Columns:</strong> {{ commandResult.summary.columns.join(', ') }}</li>
            </ul>
          </div>
          <div v-else-if="commandResult?.error">
            <p class="error">{{ commandResult.error }}</p>
          </div>
          <div v-if="showPlot">
            <div ref="plotDiv" style="width:100%;min-height:400px;"></div>
          </div>
        </section>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'UploadZone',
    data() {
      return {
        allowedFileTypes: '.csv,.xls,.xlsx',
        files: [],
        uploading: false,
        hasInvalidFiles: false,
        uploadResult: null,
        userCommand: '',
        commandResult: null,
        showPlot: false
      };
    },
    methods: {
      openFileDialog() {
        this.$refs.fileInput.click();
      },
      handleFiles(event) {
        this.files = Array.from(event.target.files);
        this.hasInvalidFiles = this.files.some(file => !this.isValidFile(file));
      },
      isValidFile(file) {
        const allowedExtensions = ['csv', 'xls', 'xlsx'];
        const fileExtension = file.name.split('.').pop().toLowerCase();
        return allowedExtensions.includes(fileExtension);
      },
      formatFileSize(size) {
        return `${(size / 1024).toFixed(2)} KB`;
      },
      async uploadFiles() {
        if (!this.files.length) return;
  
        this.uploading = true;
        this.uploadResult = null;
        this.commandResult = null;
        this.showPlot = false;
  
        try {
          const formData = new FormData();
          this.files.forEach(file => formData.append('files', file));
  
          const response = await fetch('http://localhost:8000/upload', {
            method: 'POST',
            body: formData
          });
          this.uploadResult = await response.json();
        } catch (error) {
          console.error('Upload error:', error);
          this.uploadResult = { error: 'Upload failed' };
        } finally {
          this.uploading = false;
        }
      },
      async sendCommand() {
        if (!this.userCommand.trim() || !this.uploadResult?.preview?.length) return;
  
        // Plot command detection
        if (this.userCommand.toLowerCase().startsWith('plot') || this.userCommand.toLowerCase().startsWith('heatmap')) {
          this.showPlot = true;
          this.commandResult = null;
        } else {
          this.showPlot = false;
        }
  
        try {
          const response = await fetch('http://localhost:8000/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              command: this.userCommand,
              preview: this.uploadResult.preview
            })
          });
          this.commandResult = await response.json();
          
          // Handle plot image if present
          if (this.commandResult?.plot_image) {
            this.$nextTick(() => {
              const plotDiv = this.$refs.plotDiv;
              if (plotDiv) {
                plotDiv.innerHTML = `<img src="${this.commandResult.plot_image}" alt="${this.commandResult.title}" style="width:100%;max-width:800px;height:auto;" />`;
              }
            });
          }
        } catch (error) {
          console.error('Command error:', error);
          this.commandResult = { error: 'Command failed' };
        }
      }
    }
  };
  </script>

<style scoped>
.upload-zone {
  min-height: 100vh;
  width: 100vw;
  background: linear-gradient(120deg, #ff6a00 0%, #ee0979 25%, #2196f3 60%, #00c3ff 100%);
  display: flex;
  align-items: stretch;
  justify-content: stretch;
}
.container {
  background: rgba(255,255,255,0.95);
  border-radius: 10px;
  box-shadow: 0 8px 32px 0 rgba(31,38,135,0.15);
  padding: 2.5rem 2rem;
  width: 100vw;
  min-height: 100vh;
  margin: 0;
  box-sizing: border-box;
}
.title {
  font-size: 2.5rem;
  font-weight: bold;
  color: #4f46e5;
  margin-bottom: 0.5rem;
  text-align: center;
}
.subtitle {
  color: #4b5563;
  font-size: 1.125rem;
  margin-bottom: 2rem;
  text-align: center;
}
.file-upload {
  margin-bottom: 1.5rem;
  text-align: center;
}
.file-label {
  display: block;
  margin-bottom: 1rem;
  color: #3730a3;
  font-weight: 500;
}
.main-btn {
  padding: 0.5rem 1.25rem;
  background: #6366f1;
  color: white;
  border-radius: 0.5rem;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 1rem;
  margin: 0.5rem 0;
}
.main-btn:hover {
  background: #4338ca;
}
.upload-btn {
  display: block;
  margin: 1.5rem auto 2.5rem auto;
  background: linear-gradient(90deg, #a78bfa 0%, #6366f1 100%);
  font-weight: 600;
  border-radius: 1rem;
  box-shadow: 0 2px 8px rgba(99,102,241,0.15);
}
.file-list {
  margin-bottom: 1.5rem;
}
.file-list ul {
  list-style: disc inside;
  color: #374151;
  padding-left: 1.5rem;
}
.file-list .error {
  color: #dc2626;
  margin-left: 0.5rem;
}
.result-summary {
  margin-bottom: 2rem;
}
.result-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem 1.5rem;
  color: #1e293b;
  margin-bottom: 1.5rem;
}
.table-wrapper {
  overflow-x: auto;
  border-radius: 0.5rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  border: 1px solid #e5e7eb;
  margin-bottom: 1.5rem;
}
.styled-table {
  min-width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}
.styled-table th {
  background: #1e3a8a;
  color: #fff;
  font-weight: bold;
  border: 1px solid #3b82f6;
}
.styled-table td {
  border: 1px solid #3b82f6;
  color: #111827;
}
.styled-table tbody tr:nth-child(even) {
  background: #e0f2fe;
}
.styled-table tbody tr:nth-child(odd) {
  background: #fff;
}
.styled-table tbody tr:hover {
  background: #bae6fd;
  transition: background 0.2s;
}
.command-box {
  margin-bottom: 2rem;
}
.command-input {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.command-input input[type="text"] {
  flex: 1;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  outline: none;
  font-size: 1rem;
}
.command-result {
  margin-top: 2rem;
}
.command-result .error {
  color: #dc2626;
  font-weight: 600;
}
@media (max-width: 700px) {
  .container {
    padding: 1rem 0.5rem;
  }
  .result-grid {
    grid-template-columns: 1fr;
  }
}
</style>