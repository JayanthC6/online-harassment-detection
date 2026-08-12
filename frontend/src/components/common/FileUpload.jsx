import { useRef } from 'react';
import PropTypes from 'prop-types';
import { File } from 'lucide-react';

export default function FileUpload({
  file,
  onFileSelect,
  accept,
  icon,
  activeClasses,
  titleText,
  subtitleText,
  supportedText,
}) {
  const fileRef = useRef(null);

  const handleFileDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    const droppedFile = e.dataTransfer?.files?.[0];
    if (droppedFile) {
      onFileSelect(droppedFile);
    }
  };

  return (
    <div
      className={`drop-zone ${file ? (activeClasses?.container || '') : ''}`}
      onDragOver={(e) => {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
      }}
      onDragLeave={(e) => e.currentTarget.classList.remove('dragover')}
      onDrop={handleFileDrop}
      onClick={() => fileRef.current?.click()}
    >
      <input
        ref={fileRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => onFileSelect(e.target.files?.[0] || null)}
      />
      {file ? (
        <div className="space-y-1.5 flex flex-col items-center">
          <div className="p-2 bg-panel border border-slate-700 mb-1 inline-flex">
            <File className="text-slate-400" size={24} />
          </div>
          <p className={`text-sm ${activeClasses?.text || 'text-off-white'} font-bold font-mono truncate max-w-xs px-4`}>{file.name}</p>
          <p className="text-xs text-slate-500 font-mono">
            {(file.size / (1024 * 1024)).toFixed(1)} MB <span className="opacity-50 mx-1">•</span> <span className="hover:underline cursor-pointer">click to change</span>
          </p>
        </div>
      ) : (
        <div className="space-y-2 flex flex-col items-center">
          <div className="mb-2">
            {icon}
          </div>
          <p className="text-sm font-bold text-slate-400 font-mono">{titleText}</p>
          <p className="text-xs text-slate-500 font-mono">{supportedText}</p>
        </div>
      )}
    </div>
  );
}

FileUpload.propTypes = {
  file: PropTypes.instanceOf(File),
  onFileSelect: PropTypes.func.isRequired,
  accept: PropTypes.string.isRequired,
  icon: PropTypes.node.isRequired,
  activeClasses: PropTypes.shape({
    container: PropTypes.string,
    text: PropTypes.string,
  }),
  titleText: PropTypes.string.isRequired,
  subtitleText: PropTypes.string,
  supportedText: PropTypes.string.isRequired,
};
