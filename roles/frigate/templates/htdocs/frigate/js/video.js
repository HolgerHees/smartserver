mx.Video = (function( ret ) {
    let reconnectTimeout = 5000;
    let videoUrl = null;
    let sourceBuffer = null;
    let videoElement = null;
    let mediaSource = null;
    let fifo = [];
    let reinitTimer = null;
    let socket = null;

    function processQueue()
    {
        if( fifo.length == 0 || sourceBuffer.updating ) return;

        appendToBuffer(fifo.shift());
    }

    function appendToBuffer(data)
    {
        sourceBuffer.appendBuffer(data);

        if (videoElement.paused) videoElement.play();
    }

    function onSourceBufferUpdateEnd()
    {
        const bufferLength = sourceBuffer.buffered.length;
        if (bufferLength != 0)
        {
            if (sourceBuffer.buffered.end(0) - videoElement.currentTime > 0.5) {
                videoElement.currentTime = sourceBuffer.buffered.end(0);
                console.log("Update currentTime!!!!");
            }
        }
        processQueue();
    }

    function onMediaSourceOpen()
    {
        socket = new WebSocket(videoUrl);
        socket.onerror=function(event){
            socket.close();
            setTimeout(onMediaSourceOpen, reconnectTimeout);
        }
        socket.binaryType = "arraybuffer";
        socket.addEventListener("open", (event) => {
            socket.send('{"type":"mse","value":"avc1.640029,avc1.64002A,avc1.640033,mp4a.40.2,mp4a.40.5,flac,opus"}');
        });
        socket.addEventListener("message", (event) => {
            if( typeof event.data == "string" )
            {
                let metadata = JSON.parse(event.data);
                sourceBuffer = mediaSource.addSourceBuffer(metadata["value"]);
                sourceBuffer.addEventListener("updateend", onSourceBufferUpdateEnd);
            }
            else {
                if (event.data)
                {
                    if( fifo.length == 0 && !sourceBuffer.updating )
                    {
                        appendToBuffer(event.data);
                    }
                    else
                    {
                        fifo.push(event.data);
                        processQueue();
                    }

                    window.clearTimeout(reinitTimer);
                    reinitTimer = window.setTimeout(reinitStream, 1000);
                }
            }
        });
    }

    function reinitStream()
    {
        if( socket != null )
        {
            socket.close();
            socket = null;
        }

        if( sourceBuffer != null )
        {
            mediaSource.removeSourceBuffer(sourceBuffer)
            sourceBuffer = null;
        }

        videoElement.currentTime = 0;

        initStream();
    }

    function initStream()
    {
        mediaSource = new MediaSource();
        videoElement.src = window.URL.createObjectURL(mediaSource);
        mediaSource.addEventListener("sourceopen", onMediaSourceOpen);
    }

    ret.build = function(element, url)
    {
         videoElement = element;
         videoUrl = url;

         initStream();
    }

    return ret;
})( mx.Video || {} );
