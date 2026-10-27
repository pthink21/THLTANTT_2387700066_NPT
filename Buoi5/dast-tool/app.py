from flask import Flask, jsonify, request
from runtime_monitor import RuntimeMonitor
from memory_analyzer import MemoryAnalyzer
from network_traffic_analyzer import NetworkTrafficAnalyzer
from security_behavior_checker import SecurityBehaviorChecker

def create_app(monitor=None, memory=None, network=None):
    app=Flask(__name__); app.config["MAX_CONTENT_LENGTH"]=16*1024
    monitor=monitor or RuntimeMonitor(); memory=memory or MemoryAnalyzer(); network=network or NetworkTrafficAnalyzer()
    checker=SecurityBehaviorChecker(); monitor.start(); memory.start()
    @app.get("/api/health")
    def health(): return jsonify({"status":"ok","bind":"127.0.0.1","monitoring":monitor.started})
    @app.get("/api/status")
    def status(): return jsonify({"memory":memory.snapshot(),"network":network.connections()})
    @app.get("/api/events")
    def events():
        try: limit=int(request.args.get("limit","100"))
        except ValueError: return jsonify({"error":"limit phải là số nguyên 1..200"}),400
        if not 1<=limit<=200: return jsonify({"error":"limit phải nằm trong khoảng 1..200"}),400
        return jsonify({"events":monitor.events()[-limit:]})
    @app.get("/api/alerts")
    def alerts(): return jsonify({"alerts":checker.check(monitor.events())})
    @app.post("/api/demo/event")
    def demo_event():
        data=request.get_json(silent=True)
        allowed={"process.spawn","command.shell","demo.normal"}
        if not isinstance(data,dict) or set(data)!={"type"} or data.get("type") not in allowed:
            return jsonify({"error":"body cần type thuộc allow-list demo"}),400
        monitor.record(data["type"],{"source":"local-demo-endpoint"})
        return jsonify({"recorded":data["type"]}),201
    return app

if __name__=="__main__": create_app().run(host="127.0.0.1",port=5055,debug=False)
