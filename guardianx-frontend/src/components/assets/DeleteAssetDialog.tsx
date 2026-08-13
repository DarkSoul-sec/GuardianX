import { Button, Modal } from "@/shared/components";

interface Props {
  open: boolean;
  assetName?: string;
  loading?: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export default function DeleteAssetDialog({
  open,
  assetName,
  loading = false,
  onClose,
  onConfirm,
}: Props) {
  return (
    <Modal open={open} onClose={onClose} titleId="delete-asset-title">
      <div className="max-w-md p-8">
        <h2 id="delete-asset-title" className="text-xl font-bold text-red-500">Delete Asset</h2>

        <p className="mt-4 text-slate-300">
          Are you sure you want to delete{" "}
          <span className="font-semibold">{assetName}</span>?
        </p>

        <p className="mt-2 text-sm text-red-400">
          This will permanently remove all scans, scan results and findings
          associated with this asset.
        </p>

        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="danger" disabled={loading} onClick={onConfirm}>
            {loading ? "Deleting..." : "Delete"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
