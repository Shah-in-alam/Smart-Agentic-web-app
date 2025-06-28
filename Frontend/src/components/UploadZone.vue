<template>
    <div class="upload-zone">
      <div class="container">
        <div class="header-section">
          <h1 class="title">
            <span class="title-icon">🚀</span>
            Smart Agentic Web App
          </h1>
          <p class="subtitle">Upload, analyze, and visualize your data with AI-powered insights</p>
          <div class="feature-badges">
            <span class="badge">📊 Data Analysis</span>
            <span class="badge">🎨 Visualizations</span>
            <span class="badge">🤖 AI Commands</span>
          </div>
        </div>
  
        <section class="file-upload-section">
          <div class="upload-card">
            <div class="upload-icon">📁</div>
            <label class="file-label">Upload CSV/XLS Files</label>
            <p class="upload-hint">Drag & drop or click to select files</p>
            <input ref="fileInput" type="file" multiple @change="handleFiles" :accept="allowedFileTypes" id="fileInput" style="display: none;" />
            <button @click="openFileDialog" class="select-btn">
              <span class="btn-icon">📂</span>
              Select Files
            </button>
          </div>
        </section>
  
        <section v-if="files.length > 0" class="file-list-section">
          <div class="file-list-card">
            <h3 class="section-title">
              <span class="title-icon">📋</span>
              Selected Files
            </h3>
            <div class="file-items">
              <div v-for="(file, index) in files" :key="index" class="file-item">
                <div class="file-info">
                  <span class="file-icon">📄</span>
                  <div class="file-details">
                    <strong class="file-name">{{ file.name }}</strong>
                    <span class="file-size">{{ formatFileSize(file.size) }}</span>
                  </div>
                </div>
                <span v-if="!isValidFile(file)" class="error-badge">❌ Invalid</span>
                <span v-else class="valid-badge">✅ Valid</span>
              </div>
            </div>
          </div>
        </section>
  
        <button @click="uploadFiles" :disabled="files.length === 0 || uploading || hasInvalidFiles" class="upload-btn">
          <span v-if="uploading" class="loading-spinner"></span>
          <span v-else class="btn-icon">🚀</span>
          <span v-if="uploading">Processing...</span>
          <span v-else>Upload & Analyze</span>
        </button>
  
        <section v-if="uploadResult && !uploadResult.error" class="result-section">
          <div class="result-card">
            <h3 class="section-title">
              <span class="title-icon">📊</span>
              Analysis Results
            </h3>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-number">{{ uploadResult.total_files_received }}</div>
                <div class="stat-label">Files Received</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ uploadResult.files_processed }}</div>
                <div class="stat-label">Files Processed</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ uploadResult.errors?.length || 0 }}</div>
                <div class="stat-label">Errors</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ uploadResult.summary?.total_rows || 0 }}</div>
                <div class="stat-label">Total Rows</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ uploadResult.summary?.total_columns || 0 }}</div>
                <div class="stat-label">Total Columns</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ uploadResult.summary?.memory_usage || 'N/A' }}</div>
                <div class="stat-label">Memory Usage</div>
              </div>
            </div>
  
            <div class="preview-section">
              <h4 class="preview-title">
                <span class="title-icon">👁️</span>
                Data Preview
              </h4>
              <div class="table-container">
                <table class="data-table">
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
            </div>
          </div>
        </section>
  
        <section v-if="uploadResult?.preview?.length" class="command-section">
          <div class="command-card">
            <h3 class="section-title">
              <span class="title-icon">💬</span>
              AI Command Interface
            </h3>
            <div class="command-input-group">
              <input 
                type="text" 
                v-model="userCommand" 
                placeholder="Try: 'show 10 rows' or 'plot top 10 ColumnName' or 'heatmap Col1 Col2'" 
                @keyup.enter="sendCommand"
                class="command-input"
              />
              <button @click="sendCommand" class="command-btn">
                <span class="btn-icon">⚡</span>
                Execute
              </button>
            </div>
            <div class="command-examples">
              <span class="example-tag">show 5 rows</span>
              <span class="example-tag">plot top 10 Status</span>
              <span class="example-tag">heatmap Category Status</span>
            </div>
          </div>
        </section>
  
        <section v-if="commandResult" class="command-result-section">
          <div class="result-card">
            <h3 class="section-title">
              <span class="title-icon">🎯</span>
              Command Results
            </h3>
            
            <div v-if="commandResult?.result" class="result-content">
              <div class="table-container">
                <table class="data-table">
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
            
            <div v-else-if="commandResult?.summary" class="summary-content">
              <div class="summary-grid">
                <div class="summary-item">
                  <strong>Shape:</strong> {{ commandResult.summary.shape[0] }} rows × {{ commandResult.summary.shape[1] }} cols
                </div>
                <div class="summary-item">
                  <strong>Columns:</strong> {{ commandResult.summary.columns.join(', ') }}
                </div>
              </div>
            </div>
            
            <div v-else-if="commandResult?.error" class="error-content">
              <div class="error-message">
                <span class="error-icon">⚠️</span>
                {{ commandResult.error }}
              </div>
            </div>
            
            <div v-if="showPlot" class="plot-container">
              <div ref="plotDiv" class="plot-area"></div>
            </div>
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
          console.log('Starting upload process...');
          const formData = new FormData();
          this.files.forEach(file => {
            formData.append('files', file);
            console.log(`Added file: ${file.name} (${file.size} bytes)`);
          });
  
          console.log('Sending request to backend...');
          const response = await fetch('http://localhost:8000/upload', {
            method: 'POST',
            body: formData
          });
          
          console.log('Response received:', response.status, response.statusText);
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          this.uploadResult = await response.json();
          console.log('Upload result:', this.uploadResult);
        } catch (error) {
          console.error('Upload error:', error);
          this.uploadResult = { error: `Upload failed: ${error.message}` };
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
                plotDiv.innerHTML = `<img src="${this.commandResult.plot_image}" alt="${this.commandResult.title}" style="width:100%;max-width:800px;height:auto;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,0.1);" />`;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #4facfe 100%);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
  display: flex;
  align-items: stretch;
  justify-content: stretch;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  padding: 3rem 2.5rem;
  width: 100vw;
  min-height: 100vh;
  margin: 0;
  box-sizing: border-box;
  overflow-y: auto;
}

.header-section {
  text-align: center;
  margin-bottom: 3rem;
}

.title {
  font-size: 3rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.title-icon {
  font-size: 2.5rem;
}

.subtitle {
  color: #64748b;
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
  font-weight: 400;
}

.feature-badges {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.file-upload-section {
  margin-bottom: 2rem;
}

.upload-card {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border: 2px dashed #cbd5e1;
  border-radius: 20px;
  padding: 3rem 2rem;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
}

.upload-card:hover {
  border-color: #667eea;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.15);
}

.upload-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.file-label {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.upload-hint {
  color: #64748b;
  margin-bottom: 1.5rem;
  font-size: 1rem;
}

.select-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.select-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.4);
}

.btn-icon {
  font-size: 1.25rem;
}

.file-list-section {
  margin-bottom: 2rem;
}

.file-list-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.file-items {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-icon {
  font-size: 1.5rem;
}

.file-details {
  display: flex;
  flex-direction: column;
}

.file-name {
  color: #1e293b;
  font-weight: 600;
}

.file-size {
  color: #64748b;
  font-size: 0.875rem;
}

.valid-badge {
  background: #10b981;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
}

.error-badge {
  background: #ef4444;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
}

.upload-btn {
  display: block;
  width: 100%;
  max-width: 300px;
  margin: 2rem auto 3rem auto;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 1.25rem 2rem;
  border-radius: 16px;
  font-size: 1.25rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  box-shadow: 0 12px 32px rgba(16, 185, 129, 0.3);
}

.upload-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 16px 40px rgba(16, 185, 129, 0.4);
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top: 3px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.result-section, .command-section, .command-result-section {
  margin-bottom: 2rem;
}

.result-card, .command-card {
  background: white;
  border-radius: 20px;
  padding: 2.5rem;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-item {
  text-align: center;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 16px;
  border: 1px solid #e2e8f0;
}

.stat-number {
  font-size: 2rem;
  font-weight: 800;
  color: #667eea;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #64748b;
  font-weight: 600;
  font-size: 0.875rem;
}

.preview-section {
  margin-top: 2rem;
}

.preview-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.table-container {
  overflow-x: auto;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.data-table th {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 700;
  padding: 1rem;
  text-align: left;
  border-bottom: 2px solid #5a67d8;
}

.data-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  color: #374151;
}

.data-table tbody tr:nth-child(even) {
  background: #f8fafc;
}

.data-table tbody tr:hover {
  background: #e0f2fe;
  transition: background 0.2s ease;
}

.command-input-group {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.command-input {
  flex: 1;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 1rem 1.5rem;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s ease;
  background: #f8fafc;
}

.command-input:focus {
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.command-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1rem 1.5rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.command-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.4);
}

.command-examples {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.example-tag {
  background: #e0f2fe;
  color: #0369a1;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.example-tag:hover {
  background: #bae6fd;
  transform: translateY(-1px);
}

.summary-content {
  margin-top: 1rem;
}

.summary-grid {
  display: grid;
  gap: 1rem;
}

.summary-item {
  padding: 1rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  color: #374151;
}

.error-content {
  margin-top: 1rem;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 12px;
  color: #dc2626;
  font-weight: 600;
}

.error-icon {
  font-size: 1.25rem;
}

.plot-container {
  margin-top: 2rem;
}

.plot-area {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

@media (max-width: 768px) {
  .container {
    padding: 2rem 1rem;
  }
  
  .title {
    font-size: 2rem;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .command-input-group {
    flex-direction: column;
  }
  
  .feature-badges {
    flex-direction: column;
    align-items: center;
  }
}
</style>