interface Props {
  service: string | null;
}

export default function ServiceBadge({ service }: Props) {
  return (
    <div className="inline-flex rounded-lg bg-slate-800 px-3 py-1 text-sm">
      {service || "-"}
    </div>
  );
}
