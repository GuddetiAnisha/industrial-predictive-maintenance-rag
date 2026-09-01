from __future__ import annotations
import os
import uuid
import pandas as pd
import requests
import streamlit as st

API=os.getenv("API_URL","http://127.0.0.1:8000")
st.set_page_config(page_title="Maintenance Command Center",page_icon="⚙️",layout="wide")
st.markdown("""<style>.stApp{background:#07111f;color:#edf6ff}.block-container{padding-top:1.2rem}[data-testid=stMetric]{background:#10233a;border:1px solid #24445f;border-radius:12px;padding:12px}.card{background:#10233a;padding:14px;border-radius:10px;border-left:4px solid #31d3b4}.critical{color:#ff667d;font-weight:800}h1,h2,h3{color:#edf6ff}</style>""",unsafe_allow_html=True)

roles={"Operator":"operator-demo-key","Technician":"tech-demo-key","Administrator":"admin-demo-key"}
role=st.sidebar.selectbox("Demo role",roles)
headers={"X-API-Key":roles[role]}
def api(path,method="get",**kwargs):
    try:
        response=requests.request(method,API+path,headers={**headers,**kwargs.pop("headers",{})},timeout=60,**kwargs); response.raise_for_status(); return response.json()
    except requests.RequestException as exc: st.error(f"API error at {API}: {exc}"); st.stop()

st.title("⚙ Maintenance Command Center")
st.caption("Live digital twin · explainable failure AI · evidence RAG · work orders · alerts · governance")
machines=api("/api/machines")["machines"]
labels={f"{m['machine_id']} — {m['name']} · {m['location']}":m["machine_id"] for m in machines}
machine_id=labels[st.sidebar.selectbox("Digital twin",labels,index=list(labels.values()).index("M24"))]
page=st.sidebar.radio("Workspace",["Real dataset replay","Machine connection","Digital twin","AI copilot","Technician booking","Service operations","Work orders","Alerts","Documents","Model health","Audit"])

if page=="Real dataset replay":
    st.subheader("UCI Hydraulic Systems — real experimental data")
    status=api("/api/datasets/uci-hydraulic/status")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Recorded cycles",status["cycles"]); c2.metric("Replay cycle",status["current_cycle"]); c3.metric("Mode","Dataset replay"); c4.metric("Hardware","Not connected")
    st.success("Data source: real measurements from an experimental hydraulic test rig (UCI), replayed by this application.")
    st.warning("This is not a live Bluetooth measurement. The original dataset contains temperature and vibration but no sound channel.")
    if st.button("Replay next 60-second cycle",type="primary"):
        cycle=api("/api/datasets/uci-hydraulic/next","post"); st.session_state.uci_cycle=cycle
    if st.button("Reset replay"): api("/api/datasets/uci-hydraulic/reset","post"); st.session_state.pop("uci_cycle",None); st.rerun()
    cycle=st.session_state.get("uci_cycle")
    if cycle:
        a,b,c,d=st.columns(4)
        a.metric("Cycle",cycle["cycle"]); b.metric("Mean temperature",f"{float(cycle['temperature_mean']):.2f} °C"); c.metric("Peak vibration",f"{float(cycle['vibration_max']):.3f} mm/s"); d.metric("Pump leakage label",cycle["pump_leakage"])
        st.subheader("Official component-condition labels")
        st.write(", ".join(cycle["conditions"]))
        st.json({key:cycle[key] for key in ["cooler_condition","valve_condition","pump_leakage","accumulator_pressure","stable_flag","model_predictions","replay_timestamp"]})
    st.caption("Citation: Helwig, Pignanelli & Schütze (2015), UCI Condition Monitoring of Hydraulic Systems, DOI 10.24432/C5CW21, CC BY 4.0.")
    st.subheader("External real datasets")
    st.json(api("/api/datasets/status"))
    st.caption("NASA IMS and MIMII pump data are downloaded and processed by setup_external_real_data.cmd because their raw archives are too large to redistribute inside this ZIP.")

elif page=="Machine connection":
    st.subheader("Bluetooth machine connection")
    connection=api(f"/api/connections/{machine_id}")
    status=connection["status"]
    colors={"connected":"🟢","stale":"🟠","disconnected":"🔴","not_paired":"⚪"}
    st.markdown(f"## {colors.get(status,'⚪')} {status.replace('_',' ').upper()}")
    c1,c2,c3=st.columns(3)
    c1.metric("Transport",connection.get("transport","Bluetooth"))
    c2.metric("Signal",f"{connection.get('signal_strength')} dBm" if connection.get("signal_strength") is not None else "—")
    c3.metric("Last seen",connection.get("last_seen") or "Never")
    st.write("Device:",connection.get("device_name") or "Not paired")
    if connection.get("last_error"): st.error(connection["last_error"])
    if role!="Operator":
        with st.form("pair_device"):
            device_name=st.text_input("Bluetooth device name",f"PX400-{machine_id}")
            simulated=st.checkbox("Use simulator (no physical sensor required)",True)
            address=st.text_input("Bluetooth address","SIMULATED" if simulated else "")
            if st.form_submit_button("Pair and connect"):
                api("/api/connections/pair","post",json={"machine_id":machine_id,"device_name":device_name,"device_address":address,"simulated":simulated}); st.success("Machine connected"); st.rerun()
        if status=="connected":
            if st.button("Send test sensor heartbeat"):
                api(f"/api/connections/{machine_id}/heartbeat","post",json={"temperature":91.2,"vibration":7.4,"sound":88.1,"signal_strength":-47}); st.success("Heartbeat received")
            if st.button("Disconnect machine"): api(f"/api/connections/{machine_id}/disconnect","post"); st.rerun()
    st.info("For a physical BLE sensor, set its UUIDs in .env and run run_bluetooth_gateway.cmd in a third VS Code CMD terminal.")

elif page=="Digital twin":
    health=api(f"/api/machines/{machine_id}/health"); latest=api(f"/api/live/{machine_id}"); prediction=health["prediction"]
    st.subheader(f"{machine_id} · {health['status'].upper()}")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Live temperature",f"{latest['temperature']:.1f} °C","limit 80")
    c2.metric("Live vibration",f"{latest['vibration']:.1f} mm/s","limit 6")
    c3.metric("Live sound",f"{latest['sound']:.1f} dB","limit 90")
    c4.metric("Failure risk",f"{prediction['risk']:.0%}",prediction["failure_type"].replace("_"," "))
    if st.button("Refresh live reading"): st.rerun()
    readings=pd.DataFrame(api(f"/api/machines/{machine_id}/sensors?hours=168")["readings"]); readings["timestamp"]=pd.to_datetime(readings["timestamp"])
    st.line_chart(readings.set_index("timestamp")[["temperature","vibration","sound"]])
    st.subheader("Explainable prediction")
    explanation=health["explanation"]; st.info(explanation["summary"])
    chart=pd.DataFrame(explanation["values"]).set_index("feature"); st.bar_chart(chart)
    st.caption("Contributions show how sensor levels and trends influence the risk score.")

elif page=="AI copilot":
    if "conversation_id" not in st.session_state: st.session_state.conversation_id=str(uuid.uuid4())
    examples=["Why is Machine 24 overheating?","Show similar failures from the last 2 years","Which maintenance procedure should be followed?","Predict possible failure and provide evidence."]
    question=st.selectbox("Suggested question",examples); custom=st.text_input("Ask a follow-up")
    if st.button("Analyze",type="primary"):
        result=api("/api/ask","post",json={"question":custom or question,"machine_id":machine_id,"conversation_id":st.session_state.conversation_id})
        st.markdown(result["answer"])
        for i,c in enumerate(result["citations"],1): st.markdown(f"<div class='card'><b>[{i}] {c['title']}</b> · {c['source']} · relevance {c['score']:.2f}<br>{c['excerpt']}</div>",unsafe_allow_html=True)
    history=api(f"/api/conversations/{st.session_state.conversation_id}")["messages"]
    if history:
        with st.expander("Conversation history"):
            for msg in history: st.write(f"**{msg['role'].title()}:** {msg['content']}")

elif page=="Technician booking":
    st.subheader("Book and rate a maintenance technician")
    technicians=api("/api/technicians")["technicians"]
    cards=pd.DataFrame(technicians)
    if not cards.empty:
        cards["rating"]=cards.apply(lambda x:f"{x['average_rating']:.1f} / 5 ({x['rating_count']} reviews)",axis=1)
        st.dataframe(cards[["display_name","skills","priority_level","available","rating"]],use_container_width=True)
    available=[x for x in technicians if x["available"]]
    if available:
        with st.form("booking"):
            options={f"{x['display_name']} · {x['priority_level']} · ★ {x['average_rating']:.1f}":x["username"] for x in available}
            selected_technician=options[st.selectbox("Technician",options)]
            scheduled=st.text_input("Appointment date and time","2026-09-02T10:00:00")
            issue=st.text_area("Describe the machine problem",f"Inspect {machine_id} abnormal sensor condition")
            booking_priority=st.selectbox("Service priority",["low","medium","high","critical"])
            if st.form_submit_button("Book technician"):
                api("/api/bookings","post",json={"technician_username":selected_technician,"machine_id":machine_id,"scheduled_for":scheduled,"issue":issue,"booking_priority":booking_priority}); st.success("Booking requested")
    bookings=api("/api/bookings")["bookings"]
    st.subheader("Bookings"); st.dataframe(pd.DataFrame(bookings),use_container_width=True)
    if role in {"Technician","Administrator"} and bookings:
        with st.form("complete_booking"):
            booking_id=st.selectbox("Booking",[x["id"] for x in bookings]); booking_status=st.selectbox("Status",["confirmed","in_progress","completed","cancelled"]); notes=st.text_area("Work performed / reason for action","Inspected the machine and documented the maintenance performed.")
            if st.form_submit_button("Update booking"): api(f"/api/bookings/{booking_id}","patch",json={"status":booking_status,"completion_notes":notes}); st.success("Booking updated")
    if role=="Operator":
        completed=[x for x in bookings if x["status"]=="completed"]
        if completed:
            with st.form("rating"):
                rated_booking=st.selectbox("Completed booking",[x["id"] for x in completed]); rating=st.slider("Technician rating",1,5,5); reason=st.text_area("Reason for your rating","The technician explained the repair clearly and completed it safely.")
                if st.form_submit_button("Submit rating"): api("/api/technician-reviews","post",json={"booking_id":rated_booking,"rating":rating,"reason":reason}); st.success("Thank you for your feedback")
    if role=="Administrator" and technicians:
        st.subheader("Administrator: technician priority and availability")
        tech_user=st.selectbox("Manage technician",[x["username"] for x in technicians]); priority=st.selectbox("Technician priority level",["trainee","standard","senior","expert","emergency"]); available_flag=st.checkbox("Available for booking",True)
        if st.button("Update technician profile"): api(f"/api/technicians/{tech_user}","patch",json={"priority_level":priority,"available":available_flag}); st.success("Technician profile updated")

elif page=="Service operations":
    st.subheader("Scheduling and intelligent assignment")
    appointment=st.text_input("Planned service time","2026-09-03T10:00:00")
    recommendations=api(f"/api/technician-recommendations?machine_id={machine_id}&scheduled_for={appointment}")
    st.caption(f"Predicted skill requirement: {recommendations['failure_type'].replace('_',' ')}")
    st.dataframe(pd.DataFrame(recommendations["recommendations"]),use_container_width=True)
    if role!="Operator":
        with st.form("schedule"):
            technician=st.selectbox("Technician schedule",[x["username"] for x in api("/api/technicians")["technicians"]]); starts=st.text_input("Starts","2026-09-03T08:00:00"); ends=st.text_input("Ends","2026-09-03T17:00:00"); schedule_type=st.selectbox("Schedule type",["available","leave","training","break"])
            if st.form_submit_button("Add calendar entry"): api("/api/schedules","post",json={"technician_username":technician,"starts_at":starts,"ends_at":ends,"schedule_type":schedule_type}); st.success("Calendar updated")
    st.dataframe(pd.DataFrame(api("/api/schedules")["schedules"]),use_container_width=True)
    st.subheader("Diagnosis and cost approval")
    bookings=api("/api/bookings")["bookings"]
    if role!="Operator" and bookings:
        with st.form("approval"):
            bid=st.selectbox("Booking for estimate",[x["id"] for x in bookings]); diagnosis=st.text_area("Diagnosis","Bearing and lubrication inspection required."); cost=st.number_input("Estimated cost",0.0,100000.0,350.0); hours=st.number_input("Labour hours",0.0,1000.0,2.5)
            if st.form_submit_button("Request customer approval"): api("/api/approvals","post",json={"booking_id":bid,"diagnosis":diagnosis,"estimated_cost":cost,"labour_hours":hours}); st.success("Approval requested")
    approvals=api("/api/approvals")["approvals"]; st.dataframe(pd.DataFrame(approvals),use_container_width=True)
    if role=="Operator" and approvals:
        approval_id=st.selectbox("Approval decision",[x["id"] for x in approvals]); decision=st.selectbox("Decision",["approved","rejected"]); comment=st.text_input("Customer comment")
        if st.button("Submit decision"): api(f"/api/approvals/{approval_id}","patch",json={"status":decision,"customer_comment":comment}); st.success("Decision recorded")
    st.subheader("Spare-parts inventory")
    inventory=api("/api/inventory")["items"]; st.dataframe(pd.DataFrame(inventory),use_container_width=True)
    st.subheader("Service analytics"); analytics=api("/api/analytics/service")
    cols=st.columns(4); cols[0].metric("Bookings",analytics["total_bookings"]); cols[1].metric("Completion",f"{analytics['completion_rate']:.0%}"); cols[2].metric("Rating",analytics["average_rating"]); cols[3].metric("Low stock",analytics["inventory_low_stock"])
    notifications=api("/api/notifications")["notifications"]
    if notifications:
        st.subheader("Notifications")
        for item in notifications: st.info(item["message"])

elif page=="Work orders":
    st.subheader("Maintenance work orders")
    if role!="Operator":
        with st.form("new_order"):
            title=st.text_input("Title",f"Inspect {machine_id}"); description=st.text_area("Procedure / notes"); priority=st.selectbox("Priority",["low","medium","high","critical"]); assignee=st.text_input("Assignee","maintenance-team")
            if st.form_submit_button("Create work order"): api("/api/work-orders","post",json={"machine_id":machine_id,"title":title,"description":description,"priority":priority,"assignee":assignee}); st.success("Work order created")
    orders=api("/api/work-orders")["work_orders"]; st.dataframe(pd.DataFrame(orders),use_container_width=True)
    if role!="Operator" and orders:
        oid=st.selectbox("Work order to update",[x["id"] for x in orders]); status=st.selectbox("New status",["open","assigned","in_progress","completed","cancelled"])
        if st.button("Update status"): api(f"/api/work-orders/{oid}","patch",json={"status":status}); st.success("Updated")

elif page=="Alerts":
    health=api(f"/api/machines/{machine_id}/health")
    alerts=api("/api/alerts")["alerts"]; st.dataframe(pd.DataFrame(alerts),use_container_width=True)
    if role!="Operator" and alerts:
        aid=st.selectbox("Alert to acknowledge",[x["id"] for x in alerts if not x["acknowledged"]] or [alerts[0]["id"]])
        if st.button("Acknowledge"): api(f"/api/alerts/{aid}","patch",json={"acknowledged":True}); st.success("Acknowledged")
    st.caption("Set ALERT_WEBHOOK_URL to deliver new critical alerts to Slack or Teams-compatible webhooks. Cooldown prevents alert storms.")

elif page=="Documents":
    st.subheader("Upload and index manuals or reports")
    if role=="Operator": st.warning("Technician or administrator role required.")
    else:
        file=st.file_uploader("PDF, Markdown or text",type=["pdf","md","txt"]); dtype=st.selectbox("Document type",["manual","procedure","failure_report","technician_note"]); model=st.text_input("Machine model","PX-400")
        if file and st.button("Upload and re-index"):
            result=api("/api/documents","post",files={"file":(file.name,file.getvalue(),file.type)},data={"document_type":dtype,"machine_model":model}); st.success(result["status"])

elif page=="Model health":
    evaluation=api("/api/model/evaluation"); drift=api("/api/model/drift")
    cols=st.columns(5)
    for col,key in zip(cols,["accuracy","precision","recall","f1","false_alarm_rate"]): col.metric(key.replace("_"," ").title(),f"{evaluation[key]:.0%}")
    st.write("Evaluation source:",evaluation.get("dataset"),"—",evaluation.get("split"))
    st.subheader("Confusion matrix"); st.dataframe(pd.DataFrame(evaluation["confusion_matrix"]))
    st.subheader("Sensor drift"); st.json(drift)

else:
    if role!="Administrator": st.warning("Administrator role required.")
    else: st.dataframe(pd.DataFrame(api("/api/audit")["logs"]),use_container_width=True)
