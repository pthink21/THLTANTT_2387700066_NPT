class SecurityBehaviorChecker:
    RULES={"process.spawn":"Tiến trình con được tạo trong sandbox demo.","command.shell":"Có yêu cầu shell execution trong demo."}
    def check(self, events):
        alerts=[]
        for e in events:
            if e.get("type") in self.RULES:
                alerts.append({"rule_id":"DAST-"+e["type"].upper().replace(".","-"),"severity":"warning",
                               "description":self.RULES[e["type"]],"reason":f"Sự kiện {e['type']} cần được rà soát.","timestamp":e.get("timestamp")})
        return alerts
