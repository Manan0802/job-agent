import type { Profile } from "./api";

export type ViewId = "today" | "jobs" | "referrals" | "outreach" | "pipeline" | "setup";

/** Every view gets the same props, so the shell can render any of them. */
export type ViewProps = {
  profile: Profile;
  onGoTo: (view: ViewId) => void;
  onProfileChanged: () => void;
};
