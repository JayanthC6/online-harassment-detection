import { useState } from 'react'
import { Image as ImageIcon, Sparkles } from 'lucide-react'
import { usePredict } from '../hooks/usePredict'
import ResultDisplay from './ResultDisplay'
import Card from './common/Card'
import Button from './common/Button'
import FileUpload from './common/FileUpload'
import ErrorAlert from './common/ErrorAlert'

const ALLOWED_IMAGE = '.png,.jpg,.jpeg,.webp'

export default function ScreenshotAnalyzeForm({ onNewResult }) {
  const [imageFile, setImageFile] = useState(null)
  const { loading, error, result, predictScreenshot } = usePredict()

  const handleImageAnalyze = async () => {
    if (!imageFile) return
    const data = await predictScreenshot(imageFile)
    if (data && onNewResult) onNewResult(data)
  }

  return (
    <div className="space-y-6">
      <Card className="mt-6">
        <div className="section-title">
          Screenshot Upload
        </div>

        <FileUpload
          file={imageFile}
          onFileSelect={setImageFile}
          accept={ALLOWED_IMAGE}
          icon={<ImageIcon className="mx-auto h-8 w-8 text-slate-400 mb-2" />}
          activeClasses={{
            container: '!border-indigo-400 !bg-indigo-50/50',
            text: 'text-indigo-700'
          }}
          titleText="Drop a screenshot here or click to browse"
          supportedText="Supported: PNG, JPG, WEBP (max 10MB)"
        />

        <div className="flex justify-end mt-4">
          <Button
            onClick={handleImageAnalyze}
            disabled={!imageFile}
            loading={loading}
            loadingText="Extracting text & analyzing..."
          >
            <Sparkles size={16} /> Analyze Screenshot
          </Button>
        </div>
      </Card>

      <ErrorAlert error={error} />

      {result && <ResultDisplay result={result} />}
    </div>
  )
}
