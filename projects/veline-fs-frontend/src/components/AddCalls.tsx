import * as algokit from "@algorandfoundation/algokit-utils";
import { TransactionSignerAccount } from "@algorandfoundation/algokit-utils/types/account";
import { useWallet } from "@txnlab/use-wallet";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { AppDetails } from "@algorandfoundation/algokit-utils/types/app-client";
import { VelineContractClient } from "../contracts/VelineContract";
import { OnSchemaBreak, OnUpdate } from "@algorandfoundation/algokit-utils/types/app";
import { getAlgodConfigFromViteEnvironment, getIndexerConfigFromViteEnvironment } from "../utils/network/getAlgoClientConfigs";

interface AddCallsInterface {
  openModal: boolean;
  setModalState: (value: boolean) => void;
}

const AddCalls = ({ openModal, setModalState }: AddCallsInterface) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [contractInputA, setContractInputA] = useState<number>(0);
  const [contractInputB, setContractInputB] = useState<number>(0);

  const algodConfig = getAlgodConfigFromViteEnvironment();
  const algodClient = algokit.getAlgoClient({
    server: algodConfig.server,
    port: algodConfig.port,
    token: algodConfig.token,
  });
  const indexerConfig = getIndexerConfigFromViteEnvironment();
  const indexer = algokit.getAlgoIndexerClient({
    server: indexerConfig.server,
    port: indexerConfig.port,
    token: indexerConfig.token,
  });

  const { enqueueSnackbar } = useSnackbar();
  const { signer, activeAddress } = useWallet();

  const sendAppCall = async () => {
    setLoading(true);

    // Please note, in typical production scenarios,
    // you wouldn't want to use deploy directly from your frontend.
    // Instead, you would deploy your contract on your backend and reference it by id.
    // Given the simplicity of the starter contract, we are deploying it on the frontend
    // for demonstration purposes.
    const appDetails = {
      resolveBy: "creatorAndName",
      sender: { signer, addr: activeAddress } as TransactionSignerAccount,
      creatorAddress: activeAddress,
      findExistingUsing: indexer,
    } as AppDetails;

    const appClient = new VelineContractClient(appDetails, algodClient);
    const deployParams = {
      onSchemaBreak: OnSchemaBreak.AppendApp,
      onUpdate: OnUpdate.AppendApp,
    };
    await appClient.deploy(deployParams).catch((e: Error) => {
      enqueueSnackbar(`Error deploying the contract: ${e.message}`, { variant: "error" });
      setLoading(false);
      return;
    });

    const response = await appClient
      .add({
        a: contractInputA,
        b: contractInputB,
      })
      .catch((e: Error) => {
        enqueueSnackbar(`Error calling the contract: ${e.message}`, { variant: "error" });
        setLoading(false);
        return;
      });

    enqueueSnackbar(`Response from the contract: ${response?.return}`, { variant: "success" });
    setLoading(false);
  };

  return (
    <dialog id="AddCalls_modal" className={`modal ${openModal ? "modal-open" : ""} bg-slate-200`}>
      <form method="dialog" className="modal-box">
        <h3 className="font-bold text-lg">Add a call to the contract</h3>
        <br />
        <label className="form-label" htmlFor="contractInputA">
          Input A
        </label>
        <input
          id="contractInputA"
          className="form-input"
          type="number"
          value={contractInputA}
          onChange={(e) => setContractInputA(Number(e.target.value))}
        />
        <br />
        <label className="form-label" htmlFor="contractInputB">
          Input B
        </label>
        <input
          id="contractInputB"
          className="form-input"
          type="number"
          value={contractInputB}
          onChange={(e) => setContractInputB(Number(e.target.value))}
        />

        <div className="modal-action ">
          <button className="btn" onClick={() => setModalState(!openModal)}>
            Close
          </button>
          <button className={`btn`} onClick={sendAppCall}>
            {loading ? <span className="loading loading-spinner" /> : "Send application call"}
          </button>
        </div>
      </form>
    </dialog>
  );
};

export default AddCalls;
