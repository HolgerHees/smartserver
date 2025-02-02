mx.Video = (function( ret ) {
    ret.build = function(element, url)
    {
        let reconnectTimeout = 5000;
        let videoUrl = url;
        let videoElement = element;

        let sourceBuffer = null;
        let mediaSource = null;
        let fifo = [];
        let reinitTimer = null;
        let socket = null;

        let isRunning = false;

        function appendToBuffer(data)
        {
            sourceBuffer.appendBuffer(data);

            if (videoElement.paused) videoElement.play();
        }

        function processQueue()
        {
            if( fifo.length == 0 || sourceBuffer.updating ) return;

            appendToBuffer(fifo.shift());
        }

        function onSourceBufferUpdateEnd()
        {
            if( !isRunning ) return;

            try {
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
            catch(e)
            {
                //sourceBuffer.abort();
                console.log( "CATCHED onSourceBufferUpdateEnd" );
                reinitStream();
            }
        }

        function onWebsocketData(data)
        {
            if( !isRunning ) return;

            try {
                if( fifo.length == 0 && !sourceBuffer.updating )
                {
                    appendToBuffer(data);
                }
                else
                {
                    fifo.push(data);
                    processQueue();
                }
                window.clearTimeout(reinitTimer);
                reinitTimer = window.setTimeout(reinitStream, 15000);
            }
            catch(e)
            {
                //sourceBuffer.abort();
                console.log( "CATCHED onWebsocketData" );
                reinitStream();
            }
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
                    isRunning = true;
                }
                else {
                    if (event.data) onWebsocketData(event.data);
                }
            });
        }

        function cleanup()
        {
            isRunning = false;

            if( socket != null )
            {
                window.clearTimeout(reinitTimer);

                socket.close();
                socket = null;
            }

            /*if( sourceBuffer != null )
            {
                mediaSource.removeSourceBuffer(sourceBuffer)
                sourceBuffer = null;
            }*/

            videoElement.currentTime = 0;
        }

        function reinitStream()
        {
            cleanup();
            window.setTimeout(initStream,1000);
        }

        function initStream()
        {
            mediaSource = new MediaSource();
            videoElement.src = window.URL.createObjectURL(mediaSource);
            mediaSource.addEventListener("sourceopen", onMediaSourceOpen);
        }

        initStream();

        return {
            "cleanup": cleanup
        }
    }

    return ret;
})( mx.Video || {} );
