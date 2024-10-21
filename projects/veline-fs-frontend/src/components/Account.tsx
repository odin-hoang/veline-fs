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
    <div className="p-6 space-y-4">
      <div>
        <label className="text-sm font-medium text-gray-500">Address</label>
        <p className="text-lg font-mono text-gray-900">{ellipseAddress(activeAddress)}</p>
      </div>
      <div className="flex justify-between">
        <div>
          <label className="text-sm font-medium text-gray-500">Network</label>
          <p className="text-lg text-gray-900">{algoConfig.network === "" ? "localnet" : algoConfig.network}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-500">Balance</label>
          <p className="text-lg text-gray-900">{accountInfo / 1000000}</p>
        </div>
      </div>
      <div>
        <label className="text-sm font-medium text-gray-500">Assets</label>
        <p className="text-lg text-gray-900">
          {" "}
          {assets.map((asset) => `${asset.amount / 100000000} ${asset["unit-name"] || "VeLine"}`).join(", ")}
        </p>
      </div>
    </div>
  );
};

export default Account;
