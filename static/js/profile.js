let stream=null;
function previewImage(input){
    if(input.files&&input.files[0]){
        document.getElementById("profile-preview").src=URL.createObjectURL(input.files[0]);
    }
}
async function openCamera(){
    try{
        stream=await navigator.mediaDevices.getUserMedia({video:true});
        document.getElementById("camera-box").style.display="block";
        document.getElementById("camera").srcObject=stream;
    }catch(error){
        alert("Camera permission denied or camera is not available.");
    }
}
function capturePhoto(){
    const video=document.getElementById("camera");
    const canvas=document.getElementById("canvas");
    const preview=document.getElementById("profile-preview");
    const input=document.getElementById("camera-image");
    canvas.width=video.videoWidth;
    canvas.height=video.videoHeight;
    canvas.getContext("2d").drawImage(video,0,0,canvas.width,canvas.height);
    canvas.toBlob(function(blob){
        const file=new File([blob],"camera-photo.jpg",{type:"image/jpeg"});
        const dataTransfer=new DataTransfer();
        dataTransfer.items.add(file);
        input.files=dataTransfer.files;
        preview.src=URL.createObjectURL(blob);
        if(stream){
            stream.getTracks().forEach(track=>track.stop());
            stream=null;
        }
        document.getElementById("camera-box").style.display="none";
    },"image/jpeg");
}