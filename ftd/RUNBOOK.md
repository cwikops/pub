# FTD Restart Operational Runbook

## Purpose
This runbook provides step-by-step procedures for restarting Cisco FTD appliances in Azure using the automated pipeline.

## When to Restart FTD

### Scheduled Maintenance
- Planned maintenance windows
- Software updates requiring restart
- Configuration changes requiring restart
- Periodic maintenance schedule

### Incident Response
- Performance degradation
- Memory/CPU issues
- Unresponsive management interface
- After emergency patches

### Do NOT Restart If
- Active security incident in progress
- During business-critical operations
- Pending configuration deployments
- FMC connectivity issues

## Pre-Restart Checklist

### 1. Verify Current State
```bash
# Check FTD status from FMC
# Verify all interfaces are up
# Review recent logs for errors
# Check current traffic levels
```

- [ ] FTD is manageable from FMC
- [ ] No active deployments in progress
- [ ] No critical alerts in FMC
- [ ] Current configuration backed up
- [ ] All interfaces operational
- [ ] Traffic levels acceptable for restart

### 2. Notifications
- [ ] Notify Security Operations Center (SOC)
- [ ] Notify Network Operations Center (NOC)
- [ ] Update change management system
- [ ] Alert application teams (if needed)
- [ ] Set maintenance mode in monitoring

### 3. Backup Configuration
```bash
# From FMC, backup FTD configuration
# Export configuration to secure location
# Verify backup is complete and valid
# Document current state
```

### 4. Environment Verification
- [ ] Identify environment (Production/Staging/Development)
- [ ] Verify correct Key Vault secrets configured
- [ ] Check Azure DevOps pipeline status
- [ ] Confirm network connectivity to FTD

## Restart Procedure

### Step 1: Access Azure DevOps Pipeline

1. Navigate to Azure DevOps project
2. Go to **Pipelines**
3. Select "FTD Restart Automation" pipeline
4. Click **Run pipeline**

### Step 2: Configure Parameters

**Parameter Configuration:**

| Parameter | Value | Notes |
|-----------|-------|-------|
| FTD Environment | production/staging/development | Select appropriate environment |
| Restart Mode | GRACEFUL | Use GRACEFUL unless emergency |
| Confirm Restart | YES | Type exactly "YES" to proceed |

**Restart Mode Selection:**
- **GRACEFUL**: Standard restart with proper connection cleanup (RECOMMENDED)
- **FORCED**: Immediate restart without cleanup (EMERGENCY ONLY)

### Step 3: Execute Restart

1. Review parameter selections
2. Click **Run**
3. Monitor pipeline execution in real-time
4. Note the pipeline run ID for records

**Expected Pipeline Stages:**
1. Validation (1-2 minutes)
2. Execute Restart (2-3 minutes)
3. Post-Restart Monitoring (5-10 minutes)

### Step 4: Monitor Restart Progress

**Timeline:**

| Time | Expected Status | Action |
|------|----------------|--------|
| 0-2 min | Pipeline validation | Monitor logs |
| 2-5 min | Restart initiated | FTD becomes unreachable |
| 5-10 min | FTD booting | Wait for boot process |
| 10-15 min | Services starting | Begin verification |
| 15-20 min | Full operational | Complete verification |

**During Restart:**
- FTD management interface will be unreachable
- Network traffic will be interrupted
- FMC will show FTD as disconnected
- This is normal behavior

## Post-Restart Verification

### Step 1: Basic Connectivity (T+10 minutes)

```bash
# Test ICMP connectivity
ping <ftd-management-ip>

# Test HTTPS management interface
curl -k https://<ftd-management-ip>

# Expected: Connection successful
```

- [ ] FTD responds to ping
- [ ] HTTPS interface accessible
- [ ] SSH access available (if enabled)

### Step 2: FMC Connection (T+12 minutes)

1. Log into Firepower Management Center
2. Navigate to **Devices** > **Device Management**
3. Locate FTD device
4. Verify status shows "Connected"
5. Check last heartbeat time

- [ ] FMC shows FTD as "Connected"
- [ ] Recent heartbeat received
- [ ] No connectivity alerts

### Step 3: Interface Status (T+15 minutes)

From FTD CLI or FMC:
```bash
show interface summary
show interface ip brief
```

Verify:
- [ ] All interfaces are "up"
- [ ] IP addresses correct
- [ ] Interface statistics incrementing
- [ ] No interface errors

### Step 4: Routing Verification

```bash
show route
show route summary
```

- [ ] Default route present
- [ ] All expected routes in table
- [ ] Routing protocols converged (if applicable)
- [ ] No route flapping

### Step 5: NAT and Policy Verification

From FMC:
1. Check policy deployment status
2. Verify NAT rules active
3. Review access policy status

- [ ] Policies show as deployed
- [ ] NAT translations working
- [ ] Access rules active
- [ ] No policy errors

### Step 6: Traffic Validation

```bash
# Check connection counts
show conn count

# Monitor traffic
show traffic

# Check for errors
show logging | include error
```

Test:
- [ ] New connections establishing
- [ ] Existing services accessible
- [ ] Internet connectivity working
- [ ] Internal resources reachable

### Step 7: System Health

```bash
show cpu usage
show memory
show disk usage
show process
```

- [ ] CPU usage normal (<80%)
- [ ] Memory usage normal (<80%)
- [ ] Disk usage acceptable
- [ ] All processes running

### Step 8: Log Review

Check for:
- Startup messages
- Configuration load status
- License validation
- Service initialization
- Any error messages

- [ ] No critical errors
- [ ] Clean startup logged
- [ ] License valid
- [ ] Services initialized

## Verification Results

### Success Criteria
All items checked = **RESTART SUCCESSFUL**
- FTD responsive and manageable
- FMC connection established
- All interfaces operational
- Traffic flowing normally
- No critical errors in logs

### Proceed to Post-Restart Actions

## Post-Restart Actions

### 1. Clear Maintenance Mode
- [ ] Remove maintenance mode in monitoring
- [ ] Update change management system
- [ ] Close change ticket

### 2. Notifications
- [ ] Notify SOC restart complete
- [ ] Notify NOC verification complete
- [ ] Update application teams
- [ ] Send completion email

### 3. Documentation
- [ ] Document restart in logs
- [ ] Record any issues encountered
- [ ] Update operational notes
- [ ] File post-mortem (if issues)

### 4. Monitoring
- [ ] Monitor for 24 hours post-restart
- [ ] Watch for anomalies
- [ ] Review metrics and logs
- [ ] Confirm stability

## Rollback Procedure

If restart fails or issues occur:

### Immediate Actions
1. **Do not panic** - FTD restarts are reversible
2. **Document the issue** - Capture error messages
3. **Assess impact** - What's working? What's not?
4. **Escalate if needed** - Contact senior network engineer

### Rollback Steps

**Option 1: Second Restart Attempt**
If soft failure:
1. Wait additional 5 minutes
2. Retry connectivity tests
3. Check FTD console (if available)
4. Consider forced restart if needed

**Option 2: Configuration Restore**
If configuration issue:
1. Log into FTD via console
2. Restore previous configuration backup
3. Reload configuration
4. Verify operation

**Option 3: Azure VM Restart**
If FTD VM issue:
```bash
# Restart the underlying Azure VM
az vm restart \
  --resource-group <rg-name> \
  --name <ftd-vm-name>
```

**Option 4: Escalation**
Contact:
- Senior Network Engineer: [Contact]
- Cisco TAC: [TAC Number]
- On-Call: [On-Call Number]

## Troubleshooting

### FTD Not Responding After 15 Minutes

**Diagnosis:**
1. Check Azure VM status
2. Access FTD console (Azure Serial Console)
3. Review boot messages
4. Check for hardware/VM issues

**Resolution:**
- If VM stopped: Start Azure VM
- If boot loop: Check console for errors
- If licensing issue: Reapply license
- If persistent: Contact Cisco TAC

### FMC Connection Failed

**Diagnosis:**
1. Verify FTD management interface up
2. Check FMC reachability from FTD
3. Review FMC logs
4. Verify registration key

**Resolution:**
```bash
# From FTD CLI
configure manager add <fmc-ip> <registration-key>
```

### Traffic Not Flowing

**Diagnosis:**
1. Check interface status
2. Verify routing tables
3. Review NAT configuration
4. Check access policies

**Resolution:**
- Redeploy policies from FMC
- Verify interface configurations
- Check for asymmetric routing
- Review firewall rules

### Performance Issues Post-Restart

**Symptoms:**
- High CPU usage
- Slow response times
- Connection drops

**Actions:**
1. Review running processes
2. Check resource utilization
3. Analyze traffic patterns
4. Consider another restart
5. Engage Cisco TAC if persistent

## Emergency Procedures

### Critical Failure During Restart

If FTD fails to come back online:

**Priority 1: Restore Service**
1. Attempt console access
2. Try forced restart
3. Consider failover to standby (if HA)
4. Prepare backup FTD if available

**Priority 2: Communication**
1. Alert leadership immediately
2. Open severity 1 ticket with Cisco
3. Engage emergency response team
4. Coordinate with application owners

**Priority 3: Temporary Mitigation**
- Reroute traffic if possible
- Activate backup security controls
- Document all actions taken
- Prepare incident report

## Approval and Sign-Off

### Pre-Restart Approval Required For

- Production environments
- Business hours restarts
- Emergency maintenance
- Policy changes

**Approvers:**
- Network Manager: _________________ Date: _______
- Security Manager: ________________ Date: _______
- Change Advisory Board: ___________ Date: _______

### Post-Restart Sign-Off

**Verified By:**
- Network Engineer: _________________ Date: _______ Time: _______
- Security Engineer: ________________ Date: _______ Time: _______

**Verification Status:** ☐ Success ☐ Partial ☐ Failed

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

## Appendix

### Common FTD CLI Commands

```bash
# System status
show version
show managers
show running-config

# Interface management
show interface ip brief
show interface summary

# Connectivity
ping <ip-address>
traceroute <ip-address>

# Monitoring
show conn count
show traffic
show cpu usage
show memory

# Logging
show logging
show logging | include error
```

### FMC Navigation

- **Device Management**: Devices > Device Management
- **Policy Deployment**: Deploy > Deployment
- **Health Monitoring**: Devices > Device Management > Health Monitor
- **Event Viewer**: Analysis > Events

### Contact Information

**Escalation Contacts:**
- Network Team: network-team@company.com
- Security Team: security-team@company.com
- On-Call: +1-XXX-XXX-XXXX
- Cisco TAC: +1-800-XXX-XXXX

**Azure Resources:**
- Subscription ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- Resource Group: ftd-production-rg
- Key Vault: ftd-keyvault-prod

**Pipeline:**
- Azure DevOps Project: NetworkAutomation
- Pipeline: FTD-Restart-Automation
- Repository: ftd-restart-automation

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12 | Initial | Initial runbook creation |
|  |  |  |  |
|  |  |  |  |

---

**Document Owner:** Network Operations Team  
**Last Reviewed:** 2024-12  
**Next Review:** 2025-03
