mx.UpdateServiceTemplates = (function( ret ) {
    let outdatedProcessData = null;
    let outdatedRoleData = null;
  
    let smartserverChangeInfoCodes = {
        "missing_state": ["icon-attention red","Git pull skipped because deployment status is unknown"],
        "uncommitted_changes": ["icon-attention red","Git pull skipped due to uncommitted changes"],
        "ci_missing": ["icon-info-circled yellow","Git pull skipped due to missing CI tests"],
        "ci_pending": ["icon-info-circled yellow","Git pull skipped due to ongoing CI testing"],
        "ci_failed": ["icon-attention red","Git pull skipped due to faulty CI tests"],
        "pulled_tested": ["icon-ok green", "Git pulled and all CI tests successful"],
        "pulled_untested": ["icon-ok green", "Git pulled"]
    };
    
    let active_manuell_cmd_type_map = {
        "system_reboot": "A manually started system reboot is running",
        "daemon_restart": "A manually started daemon restart is running",
        "software_check": "A manually started software check is running",

        "update_check": "A manually started update check is running",
        "system_update_check": "A manually started system update check is running",
        "deployment_update_check": "A manually started smartserver update check is running",
        "process_check": "A manually started process check is running",

        "service_restart": "A manually started service restart is running",
        "system_update": "A manually started system update is running",
        "deployment_update": "A manually started smartserver update is running"
    }
    
    let active_service_cmd_type_map = {
        "system_reboot": "{1}System reboot{2} is running since {3} {4}",
        "daemon_restart": "{1}Daemon restart{2} is running since {3} {4}",
        "software_check": "{1}Software check{2} is running since {3} {4}",

        "update_check": "{1}Update check{2} is running since {3} {4}",
        "system_update_check": "{1}System update check{2} is running since {3} {4}",
        "deployment_update_check": "{1}Smartserver update check{2} is running since {3} {4}",
        "process_check": "{1}Process check{2} is running since {3} {4}",

        "service_restart": "{1}Service restart{2} is running since {3} {4}",
        "system_update": "{1}System update{2} is running since {3} {4}",
        "deployment_update": "{1}Smartserver update{2} is running since {3} {4}"
    }
    
    let last_cmd_type_map = {
        "system_reboot": "Last {1}system reboot{2}: {3} {4}",
        "daemon_restart": "Last {1}daemon restart{2}: {3} {4}",
        "software_check": "Last {1}software check{2}: {3} {4}",

        "update_check": "Last {1}update check{2}: {3} {4}",
        "system_update_check": "Last {1}system update check{2}: {3} {4}",
        "deployment_update_check": "Last {1}smartserver update check{2}: {3} {4}",
        "process_check": "Last {1}process check{2}: {3} {4}",

        "service_restart": "Last {1}service restart{2}: {3} {4}",
        "system_update": "Last {1}system update{2}: {3} {4}",
        "deployment_update": "Last {1}smartserver update{2}: {3} {4}"
    };

    let cmd_type_map = {
        "system_reboot": "system reboot",
        "daemon_restart": "daemon restart",

        "software_check": "software check",
        "update_check": "update check",
        "system_update_check": "system update check",
        "deployment_update_check": "smartserver update check",
        "process_check": "process check",

        "service_restart": "service restart",
        "system_update": "system update",
        "deployment_update": "smartserver update"
    };

    ret.getLastFullRefresh = function(last_data_modified)
    {
        let last_update = 0;
        if( last_update == 0 || last_data_modified["processes_refreshed"] < last_update ) last_update = last_data_modified["processes_refreshed"];
        if( last_update == 0 || last_data_modified["system_updates"] < last_update ) last_update = last_data_modified["system_updates"];
        if( last_update == 0 || last_data_modified["smartserver_changes"] < last_update ) last_update = last_data_modified["smartserver_changes"];
      
        let date = null;
        let dateFormatted = null;
        let dateType = null;
        let msg = "";
        
        if( last_update > 0 )
        {
            date = new Date(last_update * 1000);
            [ dateFormatted, dateType ] = mx.UpdateServiceHelper.formatDate(date);
            msg = mx.I18N.get("Last check: {}").fill( dateFormatted ).toString().replace(": ", ": <span class='nobr'>") + "</span>";
        }
        else
        { 
            msg = mx.I18N.get("Please press 'Refresh' to check for updates for the first time");         
        }
        
        return [ date, msg ];
    }
    
    ret.setSystemOutdatedDetails = function(last_data_modified, changed_data, process_header_id, process_table_id, role_header_id, role_table_id )
    {
        let processHeaderElement = mx.$(process_header_id);
        let processTableElement = mx.$(process_table_id);

        outdatedProcessData = changed_data.hasOwnProperty("outdated_processes") ? changed_data["outdated_processes"] : outdatedProcessData;
        //outdatedProcessData = [ {'pid': 1, 'ppid': 2, 'uid': 3, 'user': 4, 'command': 5, 'service' : 6 } ];
        
        let processCount = outdatedProcessData.length;

        if( processCount > 0 )
        {
            let services = [];
            for( process in outdatedProcessData )
            {
                if( process["service"] ) services.append(process["service"]);
            }
            
            let plural = processCount > 1;
          
            let i18n_main_msg = plural ? "{} outdated processes" : "{} outdated process";
            let i18n_info_msg = plural ? "through a system update which affects these processes" : "through a system update which affects these process";
            
            processHeaderMsg = "<div class=\"info\">" + mx.I18N.get(i18n_main_msg).fill(processCount) + "<div class=\"sub\">" + mx.I18N.get(i18n_info_msg) + "</div></div><div class=\"buttons\">";
            if( services.length > 0) processHeaderMsg += "<div class=\"form button exclusive yellow\" onclick=\"mx.UpdateServiceActions.actionRestartServices(this)\" data-service=\"" + services.join(",") + "\">" + mx.I18N.get("Restart all") + "</div>";
            processHeaderMsg += "<div class=\"form button toggle\" id=\"systemProcesses\" onclick=\"mx.UpdateServiceHelper.toggleTable(this,'systemStateDetails')\"></div></div>";

            let rows = [];
            outdatedProcessData.forEach(function(process)
            {
                rows.push({
                    "columns": [
                        { "value": process["pid"] },
                        { "value": process["ppid"] },
                        { "value": process["uid"] },
                        { "value": process["user"] },
                        { "value": process["command"] },
                        { "value": process["service"] },
                        { "value": ( process["service"] ? "<div class=\"form button exclusive yellow\" onclick=\"mx.UpdateServiceActions.actionRestartServices(this)\" data-service=\"" + process["service"] + "\">" + mx.I18N.get("Restart") + "</div>" : "" ) }
                    ]
                });
            });

            let table = mx.Table.init( {
                "class": "list",
                "header": [
                    { "value": mx.I18N.get("PID") },
                    { "value": mx.I18N.get("PPID") },
                    { "value": mx.I18N.get("UID") },
                    { "value": mx.I18N.get("User") },
                    { "value": mx.I18N.get("Command"), "grow": true },
                    { "value": mx.I18N.get("Service" ) },
                    { "value": "" },
                ],
                "rows": rows
            });
            
            processHeaderElement.innerHTML = processHeaderMsg;
            processHeaderElement.style.display = "";
            
            table.build(processTableElement);
            processTableElement.style.display = "";
            
            mx.UpdateServiceHelper.initTable(processHeaderElement,processTableElement);
        }
        else
        {
            processHeaderElement.innerHTML = "";
            processHeaderElement.style.display = "none";
            processTableElement.innerHTML = "";
            processTableElement.style.display = "none";
        }
        

        outdatedRoleData = changed_data.hasOwnProperty("outdated_roles") ? changed_data["outdated_roles"] : outdatedRoleData;
        //outdatedRoleData = [ "test" ];
        
        let roleHeaderElement = mx.$(role_header_id);
        let roleTableElement = mx.$(role_table_id);

        let roleCount = outdatedRoleData.length;

        if( roleCount > 0 )
        {
            let plural = roleCount > 1;
          
            let i18n_main_msg = plural ? "{} overwritten smartserver roles" : "{} overwritten smartserver role";
            let i18n_info_msg = plural ? "through a system update which affects these roles" : "through a system update which affects these role";
            
            roleHeaderMsg = "<div class=\"info\">" + mx.I18N.get(i18n_main_msg).fill(roleCount) + "<div class=\"sub\">" + mx.I18N.get(i18n_info_msg) + "</div></div><div class=\"buttons\">";
            roleHeaderMsg += "<div class=\"form button exclusive yellow\" onclick=\"mx.UpdateServiceActions.actionDeployUpdates(this)\" data-tag=\"" + outdatedRoleData.join(",") + "\">" + mx.I18N.get("Install all") + "</div>";
            roleHeaderMsg += "<div class=\"form button toggle\" id=\"smartserverRoles\" onclick=\"mx.UpdateServiceHelper.toggleTable(this,'roleStateDetails')\"></div></div>";

            let rows = [];
            outdatedRoleData.forEach(function(role)
            {
                rows.push({
                    "columns": [
                        { "value": role },
                        { "value": ( role ? "<div class=\"form button exclusive yellow\" onclick=\"mx.UpdateServiceActions.actionDeployUpdates(this)\" data-tag=\"" + role + "\">" + mx.I18N.get("Install") + "</div>" : "" ) }
                    ]
                });
            });

            let table = mx.Table.init( {
                "class": "list",
                "header": [
                    { "value": mx.I18N.get("Role"), "grow": true },
                    { "value": "" },
                ],
                "rows": rows
            });
            
            roleHeaderElement.innerHTML = roleHeaderMsg;
            roleHeaderElement.style.display = "";
            
            table.build(roleTableElement);
            roleTableElement.style.display = "";
            
            mx.UpdateServiceHelper.initTable(roleHeaderElement,roleTableElement);
        }
        else
        {
            roleHeaderElement.innerHTML = "";
            roleHeaderElement.style.display = "none";
            roleTableElement.innerHTML = "";
            roleTableElement.style.display = "none";
        }
    }

    ret.setSystemStateDetails = function(last_data_modified, changed_data, element_id)
    {
        let element = mx.$(element_id);
        
        if( changed_data["is_reboot_needed"]["all"] )
        { 
            let reasons = {};
            if( changed_data["is_reboot_needed"]["core"] || changed_data["is_reboot_needed"]["installed"] ) reasons["1"] = mx.I18N.get("system updates");
            if( changed_data["is_reboot_needed"]["outdated"] ) reasons["2"] = mx.I18N.get("outdated processes");
                             
            let reasonKeys = Object.keys(reasons);
            let isMultiReason = reasonKeys.length > 1;
            
            let infoMsg = isMultiReason ? "Reboot necessary because of {1} and {2}" : "Reboot necessary because of {}";

            msg = "<div class=\"info\"><span class=\"icon-attention red\"></span> " + mx.I18N.get(infoMsg).fill( isMultiReason ? reasons : reasons[reasonKeys[0]] );
            
            msg += "</div><div class=\"buttons\"><div class=\"form button exclusive red\" onclick=\"mx.UpdateServiceActions.actionRebootSystem(this)\">" + mx.I18N.get("Reboot system") + "</div></div>";
            
            element.innerHTML = msg;
            element.style.display = "";
        }
        else
        {
            element.innerHTML = "";
            element.style.display = "none";
        }
    }
    
    ret.setSystemUpdateDetails = function(last_data_modified, changed_data, last_full_update, header_id, table_id)
    {
        let headerElement = mx.$(header_id);
        let tableElement = mx.$(table_id);

        //changed_data["system_updates"] = [ { 'name': 1, 'current': 2, 'update': 3, 'arch': 4 } ];
        let updateCount = changed_data["system_updates"].length;
        
        //let date = last_data_modified["system_updates"] ? new Date(last_data_modified["system_updates"] * 1000) : null;
        //if( last_full_update.getTime() == date.getTime() ) date = null;
        //const [ dateFormatted, dateType ] = mx.UpdateServiceHelper.formatDate(date);
        
        if( updateCount > 0 )
        {
            let plural = updateCount > 1;
          
            let i18n_main_msg = plural ? "{} system updates available" : "{} system update available";
            
            mx.I18N.get(i18n_main_msg).fill(updateCount)

            headerMsg = "<div class=\"info\">" + mx.I18N.get(i18n_main_msg).fill(updateCount) + "</div><div class=\"buttons\"><div class=\"form button exclusive\" onclick=\"mx.UpdateServiceActions.actionInstallUpdates(this)\">" + mx.I18N.get("Install") + "</div><div class=\"form button toggle\" onclick=\"mx.UpdateServiceHelper.toggleTable(this,'systemUpdateDetails')\"></div></div>";

            detailsMsg = "<div class=\"row\">";
            
            let update = changed_data["system_updates"][0];
            let has_current = update["current"] != null;
            
            let rows = [];
            changed_data["system_updates"].forEach(function(update)
            {
                let columns = [ { "value": update["name"] } ];
                if( has_current ) columns.push({ "value": update["current"] });
                columns.push({ "value": update["update"] });
                columns.push({ "value": update["arch"] });
                
                rows.push({"columns": columns});
            });
            
            let headerColumns = [{ "value": mx.I18N.get("Name","table") }];
            if( has_current ) headerColumns.push({ "value": mx.I18N.get("Current","table") });
            headerColumns.push({ "value": mx.I18N.get("Update","table"), "grow": true });
            headerColumns.push({ "value": mx.I18N.get("Arch","table") });

            let table = mx.Table.init( {
                "class": "list",
                "header": headerColumns,
                "rows": rows
            });
            
            headerElement.innerHTML = headerMsg;

            table.build(tableElement);
            tableElement.style.display = "";
            
            mx.UpdateServiceHelper.initTable(headerElement,tableElement);
        }
        else
        {
            headerElement.innerHTML = "<div class=\"info\">" + mx.I18N.get("No system updates available") + "</div>";
            tableElement.innerHTML = "";
            tableElement.style.display = "none";
        }
        
        return updateCount;
    }
    
    var smartserverChangesSortType = null;
    function buildSSC(type, reverse, headerElement, tableElement, data)
    {
        smartserverChangesSortType = type;
               
        let rows = [];
        if( type == 'files' )
        {
            let files = {}
            for( index in data )
            {
                let change = data[index];
                for( _index in change["files"] )
                {
                    let file = change["files"][_index];
                    if( !files.hasOwnProperty(file['path']) || file["flag"] == "A" )
                    {
                        files[file['path']] = file;
                    }
                }
            }
            
            var keys = Object.keys(files);
            keys = keys.sort();
            if( reverse ) keys = keys.reverse();
                
            for (var i=0; i<keys.length; i++) 
            {
                let file = files[keys[i]];
                rows.push({ "columns": [
                    { "value": file["flag"] },
                    { "value": file["path"], "align": "left" } 
                ]});
            }
        }
        else
        {
            let _rows = [];
            for( index in data )
            {
                let change = data[index];
                
                _rows.push( [ change["date"] ? new Date(change["date"]) : new Date(), change ] );
            }
            
            _rows.sort(function(first, second) {
                return reverse ? first[0] < second[0] : first[0] > second[0];
            });
            
            _rows.forEach(function(_row)
            {
                let change = _row[1];

                let prefix = change["date"] ? mx.UpdateServiceHelper.formatDate(new Date(change["date"]))[0] : "Aktuell";
                
                let msg = "<span style=\"font-weight:600;\">" + prefix + "</span> • " + ( change["url"] ? "<span class=\"gitCommit\" onclick=\"mx.UpdateServiceActions.openGitCommit(event,'" + change["url"] + "')\">" : "" ) + change["message"].split("\n")[0] + ( change["url"] ? "</span>" : "" );
                
                rows.push({ "columns": [ 
                    { "value": "" }, 
                    { "value": "<span style=\"margin-left: -50px;\">" + msg + "</span>", "align": "left" }
                ]});
                
                change["files"].forEach(function(file)
                {
                    rows.push({ "columns": [ 
                        { "value": file["flag"] }, 
                        { "value": file["path"], "align": "left" }
                    ]});
                });
            });
        }
        
        let table = mx.Table.init( {
            "class": "list",
            "sort": { "value": type, "reverse": reverse, "callback": function(type,reverse){ mx.UpdateServiceTemplates.sortSSC(type, reverse , headerElement, tableElement, data) } },
            "header": [
                { "value": mx.I18N.get("Flag","table"), "sort": { "value": "commits", "reverse": true } },
                { "value": mx.I18N.get("File","table"), "grow": true, "align": "left", "sort": { "value": "files" } }
            ],
            "rows": rows
        });
        
        return table;            
    }
    
    ret.sortSSC = function(type, reverse, headerElement, tableElement, data)
    {
        let table = buildSSC(type, smartserverChangesSortType != type ? ( type == 'files' ? false : true ) : reverse, headerElement, tableElement, data);
        
        table.build(tableElement);
        tableElement.style.display = "";
        
        mx.UpdateServiceHelper.initTable(headerElement,tableElement);
    }
    
    ret.setSmartserverChangeDetails = function(last_data_modified, changed_data, last_full_update, header_id, table_id)
    {
        let updateCount = changed_data["smartserver_changes"].length;
        
        //let date = last_data_modified["smartserver_changes"] ? new Date(last_data_modified["smartserver_changes"] * 1000) : null;
        //if( last_full_update.getTime() == date.getTime() ) date = null;
        //const [ dateFormatted, dateType ] = mx.UpdateServiceHelper.formatDate(date);
      
        let headerElement = mx.$(header_id);
        let tableElement = mx.$(table_id);

        if( updateCount > 0 )
        {
            let plural = updateCount > 1;
          
            let i18n_main_msg = plural ? "{} smartserver updates available" : "{} smartserver update available";
            
            headerMsg = "<div class=\"info\">" + mx.I18N.get(i18n_main_msg).fill(updateCount) + "</div><div class=\"buttons\"><div class=\"form button exclusive\" onclick=\"mx.UpdateServiceActions.actionDeployUpdates(this)\">" + mx.I18N.get("Install") + "</div><div class=\"form button toggle\" onclick=\"mx.UpdateServiceHelper.toggleTable(this,'smartserverChangeDetails')\"></div></div>";
            
            let table = buildSSC('commits',true, headerElement, tableElement, changed_data["smartserver_changes"]);

            headerElement.innerHTML = headerMsg;

            table.build(tableElement);
            tableElement.style.display = "";
            
            mx.UpdateServiceHelper.initTable(headerElement,tableElement);
        }
        else
        {
            let i18n_main_msg = "No smartserver updates available";

            headerMsg = "<div class=\"info\">" + mx.I18N.get(i18n_main_msg).fill(updateCount) + "</div><div class=\"buttons\"><div class=\"form button exclusive\" data-redeploy=1 onclick=\"mx.UpdateServiceActions.actionDeployUpdates(this)\">" + mx.I18N.get("Install again") + "</div></div>";

            headerElement.innerHTML = headerMsg;
            //headerElement.innerHTML = "<div class=\"info\">" + mx.I18N.get("No smartserver updates available") + "</div>";
            tableElement.innerHTML = "";
            tableElement.style.display = "none";
        }
        
        return updateCount;
    }
    
    ret.setSmartserverChangeState = function(last_data_modified, changed_data, element_id)
    {
        let element = mx.$(element_id);
        
        let code = changed_data["smartserver_code"];
        
        if( code )
        {           
            [iconClass,updateMsg] = smartserverChangeInfoCodes[code];
            
            msg = "<div class=\"info\"><div class=\"sub\"><span class=\"" + iconClass + "\"></span> <span style='overflow:hidden;'><span class='nobr' style='margin-right: 8px;'>" + mx.I18N.get(updateMsg);
            if( code != "missing" ) 
            {
                let date = new Date(changed_data["smartserver_pull"] * 1000);
                const [ lastPullFormatted, dateType ] = mx.UpdateServiceHelper.formatDate(date);
                subMsg = mx.I18N.get("Last git pull: {}").fill( lastPullFormatted );
              
                msg += "</span> <span class='nobr' style='margin-left: -8px;'>• " + subMsg;
            }
            msg += "</span></span></div></div>";
            
            element.innerHTML = msg;
            element.style.display = "";
        }
        else
        {
            element.innerHTML = "";
            element.style.display = "none";
        }
    }
    
    ret.getActiveServiceJobName = function(cmd_type)
    {
        return mx.I18N.get(active_service_cmd_type_map[cmd_type]);
    }
    
    ret.getActiveManuellJobName = function(cmd_type)
    {
        return mx.I18N.get(active_manuell_cmd_type_map[cmd_type]);
    }

    ret.setJobDetails = function(last_data_modified, changed_data, header_id, table_id)
    {        
        let jobs = changed_data["jobs"];
        let last_job = null;
        
        let headerElement = mx.$(header_id);
        let tableElement = mx.$(table_id);
        
        if( jobs.length > 0 )
        {
            jobs = jobs.sort(function(a,b){ return a["timestamp"] == b["timestamp"] ? 0 : ( a["timestamp"] < b["timestamp"] ? 1 : -1 ); });
          
            last_job = jobs[0];
            
            if( last_job["state"] == "running" ) jobs.shift();
        }
        
        if( jobs.length > 0 )
        {
            last_job = jobs[0];
            
            let action_msg_1 = "<span class=\"detailView\" onclick=\"mx.UpdateServiceActions.openDetails(event,'" + last_job["start"] + "','" + last_job["type"] + "','" + last_job["user"] + "')\">"
            let action_msg_2 = "</span>";
            
            let state_msg = mx.I18N.get(last_job["state"] == "success" ? "was successful" : last_job["state"]);
            let icon = last_job["state"] == "failed" || last_job["state"] == "crashed" ? "icon-attention red" : "icon-ok green";
            
            let last_job_sentence = mx.I18N.get(last_cmd_type_map[last_job["type"]]);
            let timestamp = last_job["timestamp"] + Math.round( last_job["duration"] );
            let [ dateFormatted, dateType ] = mx.UpdateServiceHelper.formatDate(  new Date(timestamp * 1000) );

            let msg = last_job_sentence.fill({"1": action_msg_1, "2": action_msg_2, "3": dateFormatted, "4": state_msg });
          
            headerMsg = "<div class=\"info\"><span class=\"" + icon + "\"></span> " + msg;
            headerMsg += "</div><div class=\"buttons\"><div class=\"form button toggle\" onclick=\"mx.UpdateServiceHelper.toggleTable(this,'lastRunningJobsDetails')\"></div></div>";

            let rows = [];
            jobs.forEach(function(job)
            {
                let date = new Date(job["timestamp"] * 1000);
                rows.push({
                    "events": { "click": function(event){ mx.UpdateServiceActions.openDetails(event,job["start"],job["type"],job["user"]); } },
                    "columns": [
                        { "class": "state " + job["state"] },
                        { "value": mx.I18N.get(cmd_type_map[job["type"]]) },
                        { "value": job["user"] },
                        { "value": mx.Logfile.formatState(job["state"]) },
                        { "value": mx.Logfile.formatDuration( job["duration"].split(".")[0] ) },
                        { "value": date.toLocaleString(), "class": "indexLogDate" },
                    ]
                });
            });

            let table = mx.Table.init( {
                "class": "list logfileBox",
                "header": [
                    { "value": "" },
                    { "value": mx.I18N.get("Job"), "grow": true },
                    { "value": mx.I18N.get("User") },
                    { "value": mx.I18N.get("State") },
                    { "value": mx.I18N.get("Duration") },
                    { "value": mx.I18N.get("Date" ) }
                ],
                "rows": rows
            });
            
            headerElement.innerHTML = headerMsg;

            table.build(tableElement);
            tableElement.style.display = "";
            
            mx.UpdateServiceHelper.initTable(headerElement,tableElement)
        }
        else
        {
            headerElement.innerHTML = "<div class=\"info\">" + mx.I18N.get("No job history available") + "</div>";
            tableElement.innerHTML = "";
            tableElement.style.display = "none";
        }
    }
    
    ret.setWorkflow = function(systemUpdatesCount, smartserverChangeCount, lastUpdateDate, element_id)
    {
        let element = mx.$(element_id);
        
        if( systemUpdatesCount > 0 || smartserverChangeCount > 0 )
        {
            let duration = (new Date()).getTime() - lastUpdateDate.getTime();
            
            let key = "";
            if( systemUpdatesCount + smartserverChangeCount > 1 ) 
            {
                key = "There are {} updates available";
            }
            else
            {
                key = "There is {} update available";
            }
            
            msg = "<div class=\"info\">" + mx.I18N.get(key).fill( systemUpdatesCount + smartserverChangeCount );
            msg += "</div><div class=\"buttons\"><div class=\"form button exclusive green\" onclick=\"mx.UpdateServiceActions.actionUpdateWorkflow(this)\">" + mx.I18N.get("Install all") + "</div></div>";
            
            element.innerHTML = msg;
        }
        else
        {
            element.innerHTML = "<div class=\"info big\">" + mx.I18N.get("Everything up to date") + "</div>";
        }
    }
    
    return ret;
})( mx.UpdateServiceTemplates || {} ); 
