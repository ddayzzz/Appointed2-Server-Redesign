var modal_process_install_html = "<h2 class=\"uk-text-large\" id=\"process_install_count\"></h2>" +
"<table class=\"uk-table uk-table-hover\"><thead><tr><th>模块名称</th><th>作者</th><th>版本</th><th>安装进度</th></tr></thead><tbody id=\"process_install_tables\"></tbody></table>" + 
"<div id=\"process_install_logs\" class=\"uk-overflow-container\" style=\"max-height: 237px;\"><h2 class=\"uk-text-large\">安装日志</h2></div><button id=\"process_install_closebtn\"class=\"uk-button uk-button-primary uk-float-right\" type=\"button\" uk-hidden>关闭</button>";
var modal_info_block = "<";

String.prototype.format = function(args) {
    var result = this;
    if (arguments.length > 0) {
        if (arguments.length == 1 && typeof (args) == "object") {
            for (var key in args) {
                if(args[key]!=undefined){
                    var reg = new RegExp("({" + key + "})", "g");
                    result = result.replace(reg, args[key]);
                }
            }
        }
        else {
            for (var i = 0; i < arguments.length; i++) {
                if (arguments[i] != undefined) {
                    var reg= new RegExp("({)" + i + "(})", "g");
                    result = result.replace(reg, arguments[i]);
                }
            }
        }
    }
    return result;
}

function process_install(returndata)
{

    // (function(modal){ modal = UIkit.modal.blockUI(model_process_install_html); 
    //     // 设置各种数据
    //     // $.ajax({
    //     //     type:'POST',
    //     //     url:'/api/package/createInstallRequests',
    //     //     contentType:'application/json',
    //     //     data:JSON.stringify(returndata.data),  // 注意需要格式化json 到字符串
    //     //     success: function(data)
    //     //     {
    //     //         alert(data);
    //     //     }
    //     // })
    //  })();
    var modal = UIkit.modal.blockUI(modal_process_install_html);
    var requestId = null;
    // 建立 Websocket 连接
    var ws = new WebSocket("ws://" + window.location.host + "/ws/package/processInstall?uploadResult=" + encodeURIComponent(JSON.stringify(returndata.data)));
    ws.onmessage = function(evt) {
        //console.log(evt.data);
        //ws.close();
        var msg = evt.data;
        
        if(msg.startsWith('BI'))
        {
            // 开头
            requestId = msg.substring(3);
            $('#process_install_logs').append('<p class="uk-text-muted uk-text-small">开始安装任务：' + requestId + '</p>');
        }
        else if(msg.startsWith('EI'))
        {
            // 安装结束，并显示结果
            var comma = msg.lastIndexOf(',');
            if(comma == -1 || comma >= msg.length)
                return;
            var res = msg.substring(comma + 8);
            var req_id = msg.substring(3, comma);
            if(res == 'Done')
            {
                $('#process_install_status_' + req_id).html('<i class=\"uk-icon-check\"></i>  安装完成');
                
            }
            else
            {
                $('#process_install_status_' + req_id).html('<i class=\"uk-icon-close \"></i>  安装失败');
            }
            $('#process_install_logs').append('<p class="uk-text-muted uk-text-small">结束安装任务：' + req_id + '</p>');
            
        }
        else if(msg.startsWith("IT"))
        {
            // 安装的模块数量
            // 添加面板
            var c = msg.substring(3, msg.length);
            document.getElementById('process_install_count').innerText = '安装包的数量：' + c;
            $('#process_install_logs').append('<p class="uk-text-muted uk-text-small">安装包数量：' + c + '</p>');
        }
        else
        {
            
            if(requestId != null)
            {
                // 这是一个安装信息
                
                var jsobj = JSON.parse(msg);
                
                // 显示界面在界面上
                $('#process_install_tables').append("<tr><td class=\"uk-text-break\">{name}</td><td class=\"uk-text-break\">{author}</td><td>{version}</td><td id=\"process_install_status_{request}\">{status}</td></tr>".format({
                    name: jsobj['name'],
                    author: jsobj['author'].replace('>','&gt;').replace('<', '&lt;'),
                    version:jsobj['version'],
                    request: requestId,
                    status: '<i class=\"uk-icon-spinner uk-icon-spin\"></i>  正在安装' 
                }));
                requestId = null;
            }
            else
            {
                // 其他消息，给用户显示
                $('#process_install_logs').append('<p class="uk-text-muted uk-text-small">' + msg + '</p>');
            }
        }

      };
      
      ws.onclose = function(evt) {
        $('#process_install_logs').append('<p class="uk-text-muted uk-text-small">服务端关闭传输</p>');
        // 显示关闭按钮
        $('#process_install_closebtn').show().bind('click', function(){
            modal.hide();
            
        });
      };
     // modal.show();
}