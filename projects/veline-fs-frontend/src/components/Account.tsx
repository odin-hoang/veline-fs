import { Asset, useWallet } from "@txnlab/use-wallet";
import { useEffect, useMemo, useState } from "react";
import { ellipseAddress } from "../utils/ellipseAddress";
import { getAlgodConfigFromViteEnvironment } from "../utils/network/getAlgoClientConfigs";

const Account = () => {
  const { activeAddress, getAccountInfo, getAssets } = useWallet();

  const [accountInfo, setAccountInfo] = useState<any>("");
  const [assets, setAssets] = useState<Asset[]>([]);

  useEffect(() => {
    if (activeAddress) {
      getAccountInfo().then((info) => {
        setAccountInfo(info.amount);
      });
    }
    if (activeAddress) {
      getAssets().then((assets) => {
        setAssets(assets);
      });
    }
  }, [activeAddress]);
  const algoConfig = getAlgodConfigFromViteEnvironment();

  const dappFlowNetworkName = useMemo(() => {
    return algoConfig.network === "" ? "sandbox" : algoConfig.network.toLocaleLowerCase();
  }, [algoConfig.network]);

  return (
    <div className="p-4 rounded-lg">
      <a
        className="text-blue-500 hover:underline"
        target="_blank"
        rel="noopener noreferrer"
        href={`https://app.dappflow.org/setnetwork?name=${dappFlowNetworkName}&redirect=explorer/account/${activeAddress}/`}
      >
        <div className="text-lg font-semibold">Address: {ellipseAddress(activeAddress)}</div>
      </a>
      <div className="mt-2 text-gray-600 grid">
        <span className="font-medium">Network: {algoConfig.network === "" ? "localnet" : algoConfig.network}</span>
        <span className="font-medium">Balance: {accountInfo / 1000000}</span>

        <span className="font-medium">
          Assets:{" "}
          <div className="text-purple-600">
            {assets.map((asset) => `${asset.amount / 100000000} ${asset["unit-name"] || "VeLine"}`).join(", ")}
          </div>
        </span>
      </div>
    </div>
  );
};

export default Account;
