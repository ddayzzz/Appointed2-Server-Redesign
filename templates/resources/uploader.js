// 参考了 http://www.jq22.com/webqd1324
//文件选择完毕时
function FilesChanged() 
{
    var op = $('#hidden_fileChooser').get(0);
    $("#progress-div").hide();
    $("#progress").html("0%").css("width","0%");
    if(op.files.length == 0)
    {
        $('#sendbtn-div').hide();
        $('#filesize-div').hide();
        
        return;
    }
    $('#sendbtn-div').show();
    var size = 0.0;
    for(var i=0; i < op.files.length; ++i)
    {
        var element = op.files[i];
        var sz = element.size / 1054000;
        size = size  + sz;
        console.log("文件类型：" + element.type); //文件类型
        console.log("文件大小（MB）：" + sz); //文件大小
    }
    $('#filesize-div').show();
    $('#filesize').text("上传的文件的大小，" + size.toFixed(2) + "MB。");

    
}
// 打开上传的对话框
function UploadFileDialog()
{
    $('#hidden_fileChooser').click();
}
//侦查附件上传情况 ,这个方法大概0.05-0.1秒执行一次
function OnProgRess(event) {
    var event = event || window.event;
    //console.log(event);  //事件对象
    console.log("已经上传：" + event.loaded); //已经上传大小情况(已上传大小，上传完毕后就 等于 附件总大小)
    //console.log(event.total);  //附件总大小(固定不变)
    var loaded = Math.floor(100 * (event.loaded / event.total)); //已经上传的百分比
    $("#progress").html(loaded + "%").css("width", loaded + "%");
}

//开始上传文件
function UploadFileFn(uploadUrl) {
    $("#progress-div").removeClass('uk-progress-danger');
    $('#progress-div').show();
    var oFiles = $("#hidden_fileChooser").get(0).files, //input file标签。上传一个文件的情况
        formData = new FormData(); //创建FormData对象
    xhr = $.ajaxSettings.xhr(); //创建并返回XMLHttpRequest对象的回调函数(jQuery中$.ajax中的方法)
    for (var i = 0; i < oFiles.length; ++i) {
        formData.append(oFiles[i].name, oFiles[i]); //添加文件对象
    }
    $.ajax({
        type: "POST",
        url: uploadUrl, // 后端服务器上传地址
        data: formData, // formData数据
        cache: false, // 是否缓存
        async: true, // 是否异步执行
        processData: false, // 是否处理发送的数据  (必须false才会避开jQuery对 formdata 的默认处理)
        contentType: false, // 是否设置Content-Type请求头
        xhr: function() {
            if (OnProgRess && xhr.upload) {
                xhr.upload.addEventListener("progress", OnProgRess, false);
                return xhr;
            }
        },
        success: function(returndata) {
            $("#progress").html("上传成功");
            $("#progress-div").removeClass('uk-progress-success');
            //alert(returndata);
            success_callback(
                
            );
        },
        error: function(returndata) {
            $("#progress").html("上传失败");
            $("#progress-div").addClass('uk-progress-danger');
            console.log(returndata);
            error_callback(returndata);
            
        }
    });
}