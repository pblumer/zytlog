export function InlineEditActions({
  onSave,
  onCancel,
  saveDisabled,
  saving,
}: {
  onSave: () => void;
  onCancel: () => void;
  saveDisabled?: boolean;
  saving?: boolean;
}) {
  return (
    <div className="actions">
      <button type="button" className="btn primary" onClick={onSave} disabled={saveDisabled || saving}>
        {saving ? 'Saving…' : 'Save'}
      </button>
      <button type="button" className="btn outline" onClick={onCancel}>
        Cancel
      </button>
    </div>
  );
}
