import { useRef } from 'react';
import PropTypes from 'prop-types';

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
      className={`drop-zone ${file ? activeClasses.container : ''}`}
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
        <div className="space-y-1">
          <p className={`text-sm ${activeClasses.text} font-medium`}>📁 {file.name}</p>
          <p className="text-xs text-gray-500">
            {(file.size / (1024 * 1024)).toFixed(1)} MB — click to change
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-2xl">{icon}</p>
          <p className="text-sm text-gray-500">{titleText}</p>
          <p className="text-xs text-gray-400">{supportedText}</p>
        </div>
      )}
    </div>
  );
}

FileUpload.propTypes = {
  file: PropTypes.instanceOf(File),
  onFileSelect: PropTypes.func.isRequired,
  accept: PropTypes.string.isRequired,
  icon: PropTypes.string.isRequired,
  activeClasses: PropTypes.shape({
    container: PropTypes.string,
    text: PropTypes.string,
  }).isRequired,
  titleText: PropTypes.string.isRequired,
  subtitleText: PropTypes.string,
  supportedText: PropTypes.string.isRequired,
};
