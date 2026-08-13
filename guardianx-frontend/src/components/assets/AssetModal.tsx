import { useEffect, useState } from "react";

import { Button, Input, Modal, Select, Textarea } from "@/shared/components";

import type { Asset, CreateAssetDto } from "@/types/asset";

interface Props {
  open: boolean;
  asset?: Asset | null;
  loading?: boolean;
  onClose: () => void;
  onSubmit: (data: CreateAssetDto) => void;
}

const initialState: CreateAssetDto = {
  name: "",
  asset_type: "SERVER",
  ip_address: "",
  domain: "",
  operating_system: "",
  environment: "Production",
  owner: "",
  criticality: "MEDIUM",
  description: "",
};

export default function AssetModal({
  open,
  asset,
  loading = false,
  onClose,
  onSubmit,
}: Props) {
  const [form, setForm] = useState<CreateAssetDto>(initialState);

  useEffect(() => {
    if (asset) {
      setForm({
        name: asset.name,
        asset_type: asset.asset_type,
        ip_address: asset.ip_address ?? "",
        domain: asset.domain ?? "",
        operating_system: asset.operating_system ?? "",
        environment: asset.environment ?? "Production",
        owner: asset.owner ?? "",
        criticality: asset.criticality ?? "MEDIUM",
        description: asset.description ?? "",
      });
    } else {
      setForm(initialState);
    }
  }, [asset]);

  function change(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) return;
    onSubmit(form);
  }

  return (
    <Modal open={open} onClose={onClose} titleId="asset-modal-title">
      <form onSubmit={submit} className="space-y-8 p-8">
        <div>
          <h1 id="asset-modal-title" className="text-3xl font-bold text-white">
            {asset ? "Edit Asset" : "Create Asset"}
          </h1>
          <p className="mt-2 text-slate-400">Register an asset inside GuardianX</p>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <Input
            name="name"
            placeholder="Asset Name"
            value={form.name}
            onChange={change}
          />
          <Input
            name="ip_address"
            placeholder="IP Address"
            value={form.ip_address}
            onChange={change}
          />
          <Input
            name="domain"
            placeholder="Domain"
            value={form.domain}
            onChange={change}
          />
          <Input
            name="owner"
            placeholder="Owner"
            value={form.owner}
            onChange={change}
          />
          <Input
            name="operating_system"
            placeholder="Operating System"
            value={form.operating_system}
            onChange={change}
          />

          <Select
            name="asset_type"
            value={form.asset_type}
            onChange={change}
            aria-label="Asset type"
          >
            <option value="SERVER">Server</option>
            <option value="WORKSTATION">Workstation</option>
            <option value="WEBSITE">Website</option>
            <option value="DOMAIN">Domain</option>
            <option value="IP_ADDRESS">IP Address</option>
            <option value="API">API</option>
            <option value="CLOUD">Cloud</option>
            <option value="MOBILE">Mobile</option>
            <option value="OTHER">Other</option>
          </Select>

          <Select
            name="environment"
            value={form.environment}
            onChange={change}
            aria-label="Environment"
          >
            <option>Production</option>
            <option>Staging</option>
            <option>Development</option>
            <option>Testing</option>
          </Select>

          <Select
            name="criticality"
            value={form.criticality}
            onChange={change}
            aria-label="Criticality"
          >
            <option>LOW</option>
            <option>MEDIUM</option>
            <option>HIGH</option>
            <option>CRITICAL</option>
          </Select>
        </div>

        <Textarea
          rows={5}
          name="description"
          value={form.description}
          onChange={change}
          placeholder="Description..."
        />

        <div className="flex justify-end gap-4">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? "Saving..." : asset ? "Update Asset" : "Create Asset"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
