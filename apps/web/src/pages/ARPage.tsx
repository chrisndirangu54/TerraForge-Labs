export function ARPage() {
  return (
    <div>
      <h2>AR Preview</h2>
      <p>WebXR launcher for deposit models and field indicator overlays.</p>
      <button
        type="button"
        onClick={() => {
          if ('xr' in navigator) {
            alert('WebXR session scaffold — connect Cesium/deposit tileset in production build.');
          } else {
            alert('WebXR not available in this browser. Use mobile AR preview.');
          }
        }}
      >
        Launch AR preview
      </button>
    </div>
  );
}