import type { ReactNode } from "react";
import { ShieldOff } from "lucide-react";

import { EmptyState, Loader } from "@/shared/components";
import { useMe } from "@/hooks/useUsers";
import type { UserRole } from "@/types/user";

interface Props {
  roles: UserRole[];
  children: ReactNode;
}

export default function RequireRole({ roles, children }: Props) {
  const { data, isLoading, error } = useMe();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader />
      </div>
    );
  }

  if (error || !data || !roles.includes(data.role)) {
    return (
      <EmptyState
        title="Access Denied"
        description="Your current role does not grant permission to view this section."
        icon={<ShieldOff size={45} />}
      />
    );
  }

  return <>{children}</>;
}
