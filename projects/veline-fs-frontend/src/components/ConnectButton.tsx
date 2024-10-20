import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Provider, useWallet } from "@txnlab/use-wallet";
import Account from "./Account";
import { ellipseAddress } from "@/utils/ellipseAddress";

export function ConnectButton() {
  const { providers, activeAddress } = useWallet();
  const isKmd = (provider: Provider) => provider.metadata.name.toLowerCase() === "kmd";
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          {activeAddress ? (
            <span className="flex items-center gap-2">
              <img
                alt={`wallet_icon_${providers?.find((p) => p.isActive)?.metadata.id}`}
                src={providers?.find((p) => p.isActive)?.metadata.icon}
                className="rounded-md w-6 h-6"
              />
              {ellipseAddress(activeAddress)}
            </span>
          ) : (
            "Connect wallet"
          )}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          {activeAddress && <span></span>}
          {!activeAddress && (
            <span>
              {" "}
              <DialogTitle>Select your wallet</DialogTitle>
              <DialogDescription>Connect your wallet to start interacting with the application.</DialogDescription>
            </span>
          )}
        </DialogHeader>
        <div className="flex items-center gap-2 justify-between">
          {activeAddress && (
            <>
              <Account />
            </>
          )}

          {!activeAddress &&
            providers?.map((provider) => (
              <Button
                variant={"veline"}
                className="h-12"
                data-test-id={`${provider.metadata.id}-connect`}
                key={`provider-${provider.metadata.id}`}
                onClick={() => {
                  return provider.connect();
                }}
              >
                {!isKmd(provider) && (
                  <img
                    alt={`wallet_icon_${provider.metadata.id}`}
                    src={provider.metadata.icon}
                    style={{ objectFit: "contain", width: "30px", height: "30px" }}
                    className="rounded-md"
                  />
                )}
                <span>{isKmd(provider) ? "LocalNet Wallet" : provider.metadata.name}</span>
              </Button>
            ))}
        </div>
        <DialogFooter>
          {activeAddress && (
            <Button
              className="btn btn-warning"
              data-test-id="logout"
              onClick={() => {
                if (providers) {
                  const activeProvider = providers.find((p) => p.isActive);
                  if (activeProvider) {
                    activeProvider.disconnect();
                  } else {
                    // Required for logout/cleanup of inactive providers
                    // For instance, when you login to localnet wallet and switch network
                    // to testnet/mainnet or vice verse.
                    localStorage.removeItem("txnlab-use-wallet");
                    window.location.reload();
                  }
                }
              }}
            >
              Logout
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
