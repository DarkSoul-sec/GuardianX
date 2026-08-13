import { Button, SearchInput } from "@/shared/components";

interface Props {
  search: string;
  onSearch: (value: string) => void;
  onAdd: () => void;
}

export default function AssetToolbar({
  search,
  onSearch,
  onAdd,
}: Props) {
  return (
    <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div className="md:max-w-md md:flex-1">
        <SearchInput value={search} onChange={onSearch} placeholder="Search assets..." />
      </div>

      <Button onClick={onAdd}>+ Add Asset</Button>
    </div>
  );
}
