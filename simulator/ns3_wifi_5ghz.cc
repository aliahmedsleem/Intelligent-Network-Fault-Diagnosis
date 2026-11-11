// Wi-Fi 2.4/5 GHz UDP experiment using ns-3 (standalone scratch program).
// Requires a supported ns-3 release with wifi, internet, mobility, applications,
// and flow-monitor modules. Results are simulated packet-level observations,
// NOT measurements from physical wireless hardware.
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/wifi-module.h"
#include <algorithm>
#include <iomanip>
#include <iostream>
#include <sstream>

using namespace ns3;

int main(int argc, char** argv) {
  std::string band = "5";
  double distance = 25.0;
  double duration = 20.0;
  double offeredMbps = 5.0;
  uint32_t seed = 1;
  uint32_t run = 1;
  CommandLine cmd;
  cmd.AddValue("band", "Wi-Fi band: 2.4 or 5 (802.11g or 802.11a)", band);
  cmd.AddValue("distance", "STA-to-AP distance in metres", distance);
  cmd.AddValue("duration", "Application measurement duration in seconds", duration);
  cmd.AddValue("offeredMbps", "UDP offered traffic Mbps", offeredMbps);
  cmd.AddValue("seed", "ns-3 random seed", seed);
  cmd.AddValue("run", "ns-3 independent run number", run);
  cmd.Parse(argc, argv);
  if ((band != "2.4" && band != "5") || distance <= 0 || distance > 1000 || duration < 2 || duration > 300 ||
      offeredMbps <= 0 || offeredMbps > 1000 || seed == 0 || run == 0) {
    std::cerr << "Invalid experiment parameters" << std::endl;
    return 2;
  }
  RngSeedManager::SetSeed(seed);
  RngSeedManager::SetRun(run);
  NodeContainer station, accessPoint;
  station.Create(1);
  accessPoint.Create(1);

  YansWifiChannelHelper channel = YansWifiChannelHelper::Default();
  YansWifiPhyHelper phy;
  phy.SetChannel(channel.Create());
  WifiHelper wifi;
  wifi.SetStandard(band == "2.4" ? WIFI_STANDARD_80211g : WIFI_STANDARD_80211a);
  wifi.SetRemoteStationManager("ns3::ConstantRateWifiManager",
                               "DataMode", StringValue("OfdmRate24Mbps"),
                               "ControlMode", StringValue("OfdmRate6Mbps"));
  WifiMacHelper mac;
  Ssid ssid = Ssid("netfault-ns3-lab");
  mac.SetType("ns3::StaWifiMac", "Ssid", SsidValue(ssid),
              "ActiveProbing", BooleanValue(false));
  NetDeviceContainer staDevice = wifi.Install(phy, mac, station);
  mac.SetType("ns3::ApWifiMac", "Ssid", SsidValue(ssid));
  NetDeviceContainer apDevice = wifi.Install(phy, mac, accessPoint);

  MobilityHelper mobility;
  Ptr<ListPositionAllocator> positions = CreateObject<ListPositionAllocator>();
  positions->Add(Vector(0.0, 0.0, 0.0));
  positions->Add(Vector(distance, 0.0, 0.0));
  mobility.SetPositionAllocator(positions);
  mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
  mobility.Install(station);
  mobility.Install(accessPoint);

  InternetStackHelper stack;
  stack.Install(station);
  stack.Install(accessPoint);
  Ipv4AddressHelper addresses;
  addresses.SetBase("10.10.0.0", "255.255.255.0");
  addresses.Assign(staDevice);
  Ipv4InterfaceContainer apIf = addresses.Assign(apDevice);

  const uint16_t port = 9000;
  PacketSinkHelper sink("ns3::UdpSocketFactory",
                        InetSocketAddress(Ipv4Address::GetAny(), port));
  ApplicationContainer sinkApp = sink.Install(accessPoint.Get(0));
  sinkApp.Start(Seconds(0.0));
  sinkApp.Stop(Seconds(duration + 3.0));

  OnOffHelper sender("ns3::UdpSocketFactory",
                     InetSocketAddress(apIf.GetAddress(0), port));
  sender.SetAttribute("DataRate", DataRateValue(DataRate(static_cast<uint64_t>(offeredMbps * 1000000))));
  sender.SetAttribute("PacketSize", UintegerValue(1200));
  sender.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  sender.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  ApplicationContainer txApp = sender.Install(station.Get(0));
  txApp.Start(Seconds(2.0));
  txApp.Stop(Seconds(duration + 2.0));

  FlowMonitorHelper monitorHelper;
  Ptr<FlowMonitor> monitor = monitorHelper.InstallAll();
  Simulator::Stop(Seconds(duration + 3.0));
  Simulator::Run();
  monitor->CheckForLostPackets();
  uint64_t txPackets = 0, rxPackets = 0, rxBytes = 0;
  double delaySumSeconds = 0.0;
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(monitorHelper.GetClassifier());
  for (const auto& [id, flow] : monitor->GetFlowStats()) {
    const auto tuple = classifier->FindFlow(id);
    if (tuple.destinationAddress != apIf.GetAddress(0) || tuple.destinationPort != port || tuple.protocol != 17) continue;
    if (flow.txPackets == 0) continue;
    txPackets += flow.txPackets;
    rxPackets += flow.rxPackets;
    rxBytes += flow.rxBytes;
    delaySumSeconds += flow.delaySum.GetSeconds();
  }
  double lossPercent = txPackets ? 100.0 * (txPackets - std::min(txPackets, rxPackets)) / txPackets : 0.0;
  double throughputMbps = 8.0 * rxBytes / (duration * 1000000.0);
  double avgDelayMs = rxPackets ? 1000.0 * delaySumSeconds / rxPackets : 0.0;
  std::cout << std::fixed << std::setprecision(5)
            << "{\"mode\":\"ns3_wifi_packet_simulation\","
            << "\"standard\":\"" << (band == "2.4" ? "802.11g_2.4ghz" : "802.11a_5ghz") << "\","
            << "\"seed\":" << seed << ",\"run\":" << run
            << ",\"distance_m\":" << distance
            << ",\"duration_s\":" << duration
            << ",\"offered_mbps\":" << offeredMbps
            << ",\"tx_packets\":" << txPackets
            << ",\"rx_packets\":" << rxPackets
            << ",\"packet_loss_percent\":" << lossPercent
            << ",\"throughput_mbps\":" << throughputMbps
            << ",\"mean_delay_ms\":" << avgDelayMs
            << "}" << std::endl;
  Simulator::Destroy();
  return 0;
}
