)export default function App() {
  const [jobId,setJobId] = useState<string>()
  const [progress,setProgress] = useState<string>()

  const handleUpload = async (file:File) => {
    const res = await fetch("/api/upload", {method:"POST",body:file})
    const {job_id}=await res.json();
    setJobId(job_id);
    const ws = new WebSocket(`ws://${location.host}/api/ws/${job_id}`);
    ws.onmessage = (ev)=>{
      const data = JSON.parse(ev.data);
      setProgress(data.state);
      if(data.state==="DONE") window.open(data.path,"_blank");
    };
  };
}
