// src/components/Home.tsx
import { useWallet } from "@txnlab/use-wallet";
import React, { useState } from "react";
import ConnectWallet from "./components/ConnectWallet";
import Transact from "./components/Transact";
import AppCalls from "./components/AppCalls";
import AddCalls from "./components/AddCalls";
import { ellipseAddress } from "./utils/ellipseAddress";
import { Button } from "./components/ui/button";
import FlickeringGrid from "./components/ui/flickering-grid";

interface HomeProps {}

const Home: React.FC<HomeProps> = () => {
  const [openWalletModal, setOpenWalletModal] = useState<boolean>(false);
  const [openDemoModal, setOpenDemoModal] = useState<boolean>(false);
  const [appCallsDemoModal, setAppCallsDemoModal] = useState<boolean>(false);
  const [addCallsDemoModal, setAddCallsDemoModal] = useState<boolean>(false);
  const { activeAddress } = useWallet();

  const toggleWalletModal = () => {
    setOpenWalletModal(!openWalletModal);
  };

  const toggleDemoModal = () => {
    setOpenDemoModal(!openDemoModal);
  };

  const toggleAppCallsModal = () => {
    setAppCallsDemoModal(!appCallsDemoModal);
  };

  const toggleAddCallsModal = () => {
    setAddCallsDemoModal(!addCallsDemoModal);
  };

  return (
    <div className="relative min-h-screen bg-teal-400">
      <div className=" text-center rounded-lg p-6 max-w-md mx-auto">
        <div className="max-w-md">
          <h1 className="text-4xl">
            Welcome to <div className="font-bold">VeLine </div>
          </h1>
          <p className="py-6">VeLine is a decentralized application that allows users to interact with the Algorand blockchain.</p>

          <div className="grid">
            <div className="divider" />
            <Button data-test-id="connect-wallet" className="btn m-2" onClick={toggleWalletModal}>
              {activeAddress ? ellipseAddress(activeAddress) : "Connect Wallet"}
            </Button>

            {activeAddress && (
              <button data-test-id="transactions-demo" className="btn m-2" onClick={toggleDemoModal}>
                Transactions Demo
              </button>
            )}

            {activeAddress && (
              <button data-test-id="appcalls-demo" className="btn m-2" onClick={toggleAppCallsModal}>
                Contract Interactions Demo
              </button>
            )}

            {activeAddress && (
              <button data-test-id="addcalls-demo" className="btn m-2" onClick={toggleAddCallsModal}>
                Add Calls Demo
              </button>
            )}
          </div>

          <ConnectWallet openModal={openWalletModal} closeModal={toggleWalletModal} />
          <Transact openModal={openDemoModal} setModalState={setOpenDemoModal} />
          <AppCalls openModal={appCallsDemoModal} setModalState={setAppCallsDemoModal} />
          <AddCalls openModal={addCallsDemoModal} setModalState={setAddCallsDemoModal} />
        </div>
      </div>
    </div>
  );
};

export default Home;
