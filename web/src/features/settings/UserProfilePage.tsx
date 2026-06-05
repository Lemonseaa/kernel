import { useQuery } from "@tanstack/react-query";
import { getUserProfile } from "../../api/client";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";

export function UserProfilePage() {
  const profile = useQuery({ queryKey: ["user-profile"], queryFn: getUserProfile });

  return (
    <>
      <PageHeader title="User Profile" description="Formal human-owned preferences and separate Hermes draft notes." />
      {profile.data ? (
        <div className="grid gap-4 xl:grid-cols-2">
          <Card title="Formal Profile">
            <pre className="whitespace-pre-wrap text-sm text-ink">{profile.data.formal_profile}</pre>
          </Card>
          <Card title="Suggested Notes">
            <pre className="whitespace-pre-wrap text-sm text-muted">{profile.data.suggested_notes}</pre>
          </Card>
        </div>
      ) : (
        <EmptyState title="No profile loaded" body="Enter an API token to load the formal user profile." />
      )}
    </>
  );
}
