import { useEffect, useRef } from 'react';

type ConfirmDialogVariant = 'danger' | 'warning' | 'info';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  variant?: ConfirmDialogVariant;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  variant = 'warning',
  confirmLabel = 'Bestätigen',
  cancelLabel = 'Abbrechen',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) {
      cancelRef.current?.focus();
    }
  }, [open]);

  if (!open) return null;

  const confirmClass = variant === 'danger' ? 'btn danger' : variant === 'warning' ? 'btn primary' : 'btn';

  return (
    <div className="modal-backdrop" onClick={onCancel} role="presentation">
      <div
        className="modal"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-message"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="confirm-dialog-title" style={{ margin: '0 0 0.5rem' }}>
          {title}
        </h3>
        <p id="confirm-dialog-message" className="meta" style={{ margin: 0 }}>
          {message}
        </p>
        <div className="actions" style={{ marginTop: '1rem' }}>
          <button type="button" className={confirmClass} onClick={onConfirm}>
            {confirmLabel}
          </button>
          <button type="button" className="btn outline" ref={cancelRef} onClick={onCancel}>
            {cancelLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
