import { useMemo, useState } from "react";
import { Server } from "lucide-react";

import AssetToolbar from "@/components/assets/AssetToolbar";
import AssetTable from "@/components/assets/AssetTable";
import AssetModal from "@/components/assets/AssetModal";
import DeleteAssetDialog from "@/components/assets/DeleteAssetDialog";

import {
  useAssets,
  useCreateAsset,
  useDeleteAsset,
  useRunScan,
  useUpdateAsset,
} from "@/hooks/useAssets";

import { Button, EmptyState } from "@/shared/components";
import { useToastContext } from "@/hooks/useToastContext";

import type { Asset } from "@/types/asset";
import type { ScanProfile } from "@/types/scan";

export default function Assets() {
  const { data = [], isLoading, error, refetch } = useAssets();

  const createAsset = useCreateAsset();
  const updateAsset = useUpdateAsset();
  const deleteAsset = useDeleteAsset();
  const runScan = useRunScan();
  const { success, error: showError } = useToastContext();

  const [search, setSearch] = useState("");
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [scanningId, setScanningId] = useState<number | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [showDelete, setShowDelete] = useState(false);

  const filteredAssets = useMemo(() => {
    return data.filter((asset) =>
      asset.name.toLowerCase().includes(search.toLowerCase())
    );
  }, [data, search]);

  function handleScan(asset: Asset, profile: ScanProfile) {
    setScanningId(asset.id);
    runScan.mutate(
      { assetId: asset.id, scanProfile: profile },
      {
        onSuccess: () => {
          success(
            `Scan launched for ${asset.name} (${profile}). It will start shortly.`
          );
        },
        onError: () => {
          showError(`Failed to launch scan for ${asset.name}.`);
        },
        onSettled: () => {
          setScanningId(null);
        },
      }
    );
  }

  return (
    <div className="space-y-6">
      <AssetToolbar
        search={search}
        onSearch={setSearch}
        onAdd={() => {
          setSelectedAsset(null);
          setShowModal(true);
        }}
      />

      {error ? (
        <EmptyState
          title="Failed to Load Assets"
          description="Unable to fetch assets. Please try again later."
          icon={<Server size={40} />}
          action={<Button onClick={() => refetch()}>Retry</Button>}
        />
      ) : (
        <AssetTable
          assets={filteredAssets}
          loading={isLoading}
          scanningId={scanningId}
          onEdit={(asset) => {
            setSelectedAsset(asset);
            setShowModal(true);
          }}
          onDelete={(asset) => {
            setSelectedAsset(asset);
            setShowDelete(true);
          }}
          onScan={handleScan}
        />
      )}

      <AssetModal
        open={showModal}
        asset={selectedAsset}
        loading={createAsset.isPending || updateAsset.isPending}
        onClose={() => setShowModal(false)}
        onSubmit={(data) => {
          if (selectedAsset) {
            updateAsset.mutate({ id: selectedAsset.id, data });
          } else {
            createAsset.mutate(data);
          }
          setShowModal(false);
        }}
      />

      <DeleteAssetDialog
        open={showDelete}
        assetName={selectedAsset?.name}
        loading={deleteAsset.isPending}
        onClose={() => setShowDelete(false)}
        onConfirm={() => {
          if (!selectedAsset) return;
          deleteAsset.mutate(selectedAsset.id);
          setShowDelete(false);
        }}
      />
    </div>
  );
}
