# Network troubleshooting runbook (synthetic example)

## OSPF neighbor stuck in EXSTART or EXCHANGE
This usually means an MTU mismatch between the two ends of the link. Compare `ip mtu` on both interfaces with `show ip interface`. Set both sides to the same value, or use `ip ospf mtu-ignore` as a temporary workaround. Then clear the neighbor with `clear ip ospf process`.

## OSPF neighbor not forming at all
Check that both interfaces are in the same subnet, that the area ID matches, and that the interface is not passive. Confirm hello and dead timers match on both sides. Look at `show ip ospf interface` and `show ip ospf neighbor`.

## BGP session stuck in Active or Idle
Confirm the neighbor IP is reachable with ping. Check that the remote AS number is correct and that an access list is not blocking TCP port 179. Verify the timers and authentication match. Use `show ip bgp summary` and `show ip bgp neighbors`.

## Users cannot reach a VLAN across the trunk
Verify the VLAN exists on both switches and is allowed on the trunk with `show interfaces trunk`. Check the native VLAN matches on both ends, since a mismatch causes spanning tree errors and dropped traffic.

## Port shows err-disabled after a security violation
Port security with violation mode shutdown disables the port when too many MAC addresses appear. Check `show port-security interface`. Remove the extra device, then run `shutdown` and `no shutdown` on the port. Use violation mode restrict if you want to log instead of disable.

## Cannot SSH to a device
Check the vty access class and the source address of your session against the management access list. Confirm `transport input ssh` is set and that the crypto keys exist.
