import { useState, useRef } from 'react'
import { usePredict } from '../hooks/usePredict'
import ResultDisplay from './ResultDisplay'
import Card from './common/Card'
import Button from './common/Button'
import FileUpload from './common/FileUpload'
import ErrorAlert from './common/ErrorAlert'

const ALLOWED_IMAGE = '.png,.jpg,.jpeg,.webp'

export default function ScreenshotAnalyzeForm({ onNewResult }) {
  const [imageFile, setImageFile] = useState(null)
  const fileRef = useRef(null)
  const { loading, error, result, predictScreenshot } = usePredict()

  const handleImageAnalyze = async () => {
    if (!imageFile) return
    const data = await predictScreenshot(imageFile)
    if (data && onNewResult) onNewResult(data)
  }

  const handleFileDrop = (e) => {
    e.preventDefault()
    e.currentTarget.classList.remove('dragover')
    const file = e.dataTransfer?.files?.[0]
    if (file) setImageFile(file)
  }

  return (
    <div className="space-y-4">
      <Card className="mt-4">
        <div className="section-title">
          <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
          Screenshot Upload
        </div>

        <FileUpload
          file={imageFile}
          onFileSelect={setImageFile}
          accept={ALLOWED_IMAGE}
          icon="🖼️"
          activeClasses={{
            container: '!border-emerald-400 !bg-emerald-50/50',
            text: 'text-emerald-700'
          }}
          titleText="Drop a screenshot here or click to browse"
          supportedText="Supported: PNG, JPG, WEBP (max 10MB)"
        />

        <div className="flex justify-end mt-3">
          <Button
            onClick={handleImageAnalyze}
            disabled={!imageFile}
            loading={loading}
            loadingText="Extracting text & analyzing..."
            style={!loading && imageFile ? { background: '#059669' } : {}}
          >
            🖼️ Analyze Screenshot
          </Button>
        </div>
      </Card>

      <ErrorAlert error={error} />

      {result && <ResultDisplay result={result} />}
    </div>
  )
}
