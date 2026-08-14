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
  const [platform, setPlatform] = useState('generic')
  const { loading, error, result, predictScreenshot } = usePredict()

  const handleImageAnalyze = async () => {
    if (!imageFile) return
    const data = await predictScreenshot(imageFile, null, platform)
    if (data && onNewResult) onNewResult(data)
  }

  return (
    <div className="space-y-6">
      <Card className="border-outline-variant mt-6">
        <div className="section-title">
          Screenshot Upload
        </div>

        <div className="mb-4">
          <label className="block text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-1">Source Platform (Optional)</label>
          <select 
            value={platform} 
            onChange={e => setPlatform(e.target.value)}
            className="input-dark w-full max-w-xs text-sm"
          >
            <option value="generic">Unknown / Other</option>
            <option value="whatsapp">WhatsApp</option>
            <option value="instagram">Instagram</option>
          </select>
        </div>

        <FileUpload
          file={imageFile}
          onFileSelect={setImageFile}
          accept={ALLOWED_IMAGE}
          icon={<ImageIcon className="mx-auto h-8 w-8 text-slate-400 mb-2" />}
          activeClasses={{
            container: '!border-off-white !bg-slate-800',
            text: 'text-off-white'
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
