// 设置数据绑定
// 设置状态属性
var routerIdToVue = new Array();
var routerStausToVue = new Array();
var sysStatusVue = null;

function init_addRequestCount() {

    // 描述组建关系
    Vue.component('request-counter-comp', {
        props: ['counter'],
        template: '<span>{{counter}}&nbsp;&nbsp;</span>'
    });
    // 路由的启动信息
    Vue.component('router-btn-comp', {
        props: ['renable', 'rchange'],
        template: '<button class="uk-button">{{renable ? "禁用": "启用"}}</button>'
    });
    // 遍历所有模块的组件，添加关联的数据绑定
    var packages = document.getElementsByClassName('packageStatus');
    for (var i = 0; i < packages.length; ++i) {
        // 对于每一个模块中的每一个路由都设置新的 Vue 实例
        var router_tag_main = packages[i].getElementsByClassName('requestCounter_class');
        for (var j = 0; j < router_tag_main.length; ++j) {
            var router_main = router_tag_main[j];
            var vm = new Vue({
                el: '#' + router_main.id,
                data: {
                    routerStatus_counter: 0,
                    routerStatus_enable: false,
                    enableChangedCallStr: ''
                },
                methods: {
                    update: function (counter, enabled, flagName) {
                        this.routerStatus_counter = counter;
                        this.routerStatus_enable = enabled;
                        if (enabled) {
                            this.enableChangedCallStr = '"false","' + flagName + '")';
                        }
                        else {
                            this.enableChangedCallStr = '"true","' + flagName + '")';
                        }
                    }
                }
            });
            routerIdToVue[router_main.id] = vm;
        }
    }
    // 初始化全局运行信息
    sysStatusVue = new Vue({
        el: '#main_sysStatusMgr',
        data: {
            status_cpuRate: '不可用',
            status_memoryUsage: '不可用',
            status_runnningTime: '不可用',
            status_bindHost: '不可用',
            status_bindPort: '不可用'
        },
        methods: {
            update: function (cpurate, mem, rtime, bindHost, bindPort) {
                this.status_cpuRate = cpurate;
                this.status_memoryUsage = mem;
                this.status_bindHost = bindHost;
                this.status_bindPort = bindPort;
                this.status_runnningTime = rtime;
            }
        }
    });
}
function getRuntimeInfo(notMaintenance) {
    axios.get('/api/maintenance/getStatus')
        .then(function (response) {
            var runtimeInfo = response.data.data.runningTimeInfo;
            if (notMaintenance) {
                var reqCount = runtimeInfo.routerInfo;
                for (var router_info in reqCount) {
                    routerIdToVue[router_info].update(reqCount[router_info].count, reqCount[router_info].enable, router_info);
                }
            }
            // 更新其他的信息
            sysStatusVue.update(runtimeInfo.cpuRate, runtimeInfo.memoryUsage, runtimeInfo.runningTime, runtimeInfo.bindHost, runtimeInfo.bindPort);
        })
        .catch(function (error) {
            alert(error);
        })
}

function toClose() {
    UIkit.modal.confirm("确定要关闭服务？", function () {
        $.ajax({
            type: "GET",
            url: '/api/main_close',
            success: function (str_response) {
                var newDoc = document.open("text/html", "replace");
                var txt = "<html><script type=\"text/javascript\" >window.onload = function () {setTimeout(() => { window.location.href = 'about:blank';}, 2000);}</script><body>服务关闭。</body></html>";
                newDoc.write(txt);
                newDoc.close();
            }
        });
    });
}
function toRestart() {
    UIkit.modal.confirm("确定要重启服务？", function () {
        $.ajax({
            type: "GET",
            url: '/api/main_restart',
            success: function (str_response) {
                var newDoc = document.open("text/html", "replace");
                var txt = "<html><script type=\"text/javascript\" >window.onload = function () {setTimeout(() => { location.reload();}, 2000);}</script><body>服务正在重启。2 秒后自动刷新。</body></html>";
                newDoc.write(txt);
                newDoc.close();
            }
        });
    });
}
function toRestartAndEnterMaintenance() {
    UIkit.modal.confirm("确定要重启服务并进入到维护模式？进入维护模式后可以对模块进行管理。", function () {
        // 点击OK确认后开始执行
        $.ajax({
            type: "GET",
            url: '/api/main_restart/enterMaintenance',
            success: function (str_response) {
                var newDoc = document.open("text/html", "replace");
                var txt = "<html><script type=\"text/javascript\" >window.onload = function () {setTimeout(() => { location.reload();}, 2000);}</script><body>服务正在重启并进入维护模式。2 秒后自动刷新。</body></html>";
                newDoc.write(txt);
                newDoc.close();
            }
        });
    });
}
function changeRouterEnableStatus(packageName, targetStatus, routerFlag) {
    // 需要启用
    axios.get('/api/maintenance/setRouterStatus/' + packageName + '/' + routerFlag + '?enable=' + targetStatus)
        .then(function (response) {
            alert('设置成功！');
            getRuntimeInfo(true);
        })
        .catch(function (error) {
            alert(error);
        })

}
