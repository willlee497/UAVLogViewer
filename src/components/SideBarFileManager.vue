<template>
    <div>
        <li  v-if="file==null && !sampleLoaded" >
            <a @click="onLoadSample('sample')" class="section"><i class="fas fa-play"></i>  Open Sample </a>
        </li>
        <li v-if="url">
            <a @click="share" class="section"><i class="fas fa-share-alt"></i> {{ shared ? 'Copied to clipboard!' :
                'Share link'}}</a>
        </li>
        <li v-if="url">
            <a :href="'/uploaded/' + url" class="section" target="_blank"><i class="fas fa-download"></i> Download</a>
        </li>
        <div @click="browse" @dragover.prevent @drop="onDrop" id="drop_zone"
        v-if="file==null && uploadpercentage===-1  && !sampleLoaded">
            <p>Drop *.tlog or *.bin file here or click to browse</p>
            <input @change="onChange" id="choosefile" style="opacity: 0;" type="file">
        </div>
        <!--<b-form-checkbox @change="uploadFile()" class="uploadCheckbox" v-if="file!=null && !uploadStarted"> Upload
        </b-form-checkbox>-->
        <VProgress v-bind:complete="transferMessage"
                   v-bind:percent="uploadpercentage"
                   v-if="uploadpercentage > -1">
        </VProgress>
        <VProgress v-bind:complete="state.processStatus"
                   v-bind:percent="state.processPercentage"
                   v-if="state.processPercentage > -1"
        ></VProgress>
    </div>
</template>
<script>
/* eslint-disable indent */
import VProgress from './SideBarFileManagerProgressBar.vue'
import Worker from '../tools/parsers/parser.worker.js'
import { store } from './Globals'
import axios from 'axios'

import { MAVLink20Processor as MAVLink } from '../libs/mavlink'

const worker = new Worker()

worker.addEventListener('message', function (event) {
})

export default {
    name: 'Dropzone',
    data: function () {
        return {
            // eslint-disable-next-line no-undef
            mavlinkParser: new MAVLink(),
            uploadpercentage: -1,
            sampleLoaded: false,
            shared: false,
            url: null,
            transferMessage: '',
            state: store,
            file: null,
            uploadStarted: false
        }
    },
    created () {
        this.$eventHub.$on('loadType', this.loadType)
        this.$eventHub.$on('trimFile', this.trimFile)
    },
    beforeDestroy () {
        this.$eventHub.$off('open-sample')
    },
    methods: {
        trimFile () {
            worker.postMessage({ action: 'trimFile', time: this.state.timeRange })
        },
        onLoadSample (file) {
            let url
            if (file === 'sample') {
                this.state.file = 'sample'
                url = require('../assets/vtol.tlog').default
                this.state.logType = 'tlog'
            } else {
                url = file
                // Set the file name for display purposes
                const urlParts = url.split('/')
                this.state.file = urlParts[urlParts.length - 1]
            }
            const oReq = new XMLHttpRequest()
            console.log(`loading file from ${url}`)

            // Set the log type based on file extension
            this.state.logType = url.indexOf('.tlog') > 0 ? 'tlog' : 'bin'
            if (url.indexOf('.txt') > 0) {
                this.state.logType = 'dji'
            }

            oReq.open('GET', url, true)
            oReq.responseType = 'arraybuffer'

            // Use arrow function to preserve 'this' context
            oReq.onload = (oEvent) => {
                const arrayBuffer = oReq.response
                this.transferMessage = 'Download Done'
                this.sampleLoaded = true
                // Parse locally for immediate display
                worker.postMessage({
                    action: 'parse',
                    file: arrayBuffer,
                    isTlog: (url.indexOf('.tlog') > 0),
                    isDji: (url.indexOf('.txt') > 0)
                })
                // Also upload to backend to create session ID for chat
                const blob = new Blob([arrayBuffer])
                const form = new FormData()
                form.append('file', blob, this.state.file + '.' + this.state.logType)
                axios.post('/upload-log', form, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                })
                .then(resp => {
                    store.currentSessionId = resp.data.session_id
                    store.chatHistory = []
                    console.log('Sample file uploaded for chat, session ID:', resp.data.session_id)
                })
                .catch(err => {
                    console.error('Failed to upload sample for chat:', err)
                    // Don't alert here as the file still works for viewing
                })
            }
            oReq.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    this.uploadpercentage = 100 * e.loaded / e.total
                }
            }
            , false)
            oReq.onerror = (error) => {
                alert('unable to fetch remote file, check CORS settings in the target server')
                console.log(error)
            }

            oReq.send()
        },
        onChange (ev) {
            const fileinput = document.getElementById('choosefile')
            this.process(fileinput.files[0])
        },
        onDrop (ev) {
            // Prevent default behavior (Prevent file from being opened)
            ev.preventDefault()
            if (ev.dataTransfer.items) {
                // Use DataTransferItemList interface to access the file(s)
                for (let i = 0; i < ev.dataTransfer.items.length; i++) {
                    // If dropped items aren't files, reject them
                    if (ev.dataTransfer.items[i].kind === 'file') {
                        const file = ev.dataTransfer.items[i].getAsFile()
                        this.process(file)
                    }
                }
            } else {
                // Use DataTransfer interface to access the file(s)
                for (let i = 0; i < ev.dataTransfer.files.length; i++) {
                    console.log('... file[' + i + '].name = ' + ev.dataTransfer.files[i].name)
                    console.log(ev.dataTransfer.files[i])
                }
            }
        },
        loadType: function (type) {
            // Don't send loadType to worker for TLOG files
            if (this.state.logType === 'tlog') {
                console.log('Skipping loadType for TLOG file:', type)
                return
            }
            worker.postMessage({
                action: 'loadType',
                type: type
            })
        },
        process: function (file) {
            this.state.file = file.name
            this.state.processStatus = 'Pre-processing...'
            this.state.processPercentage = 100
            const form = new FormData()
            form.append('file', file)
            const isTlogFile = file.name.toLowerCase().endsWith('.tlog')
            axios.post('/upload-log', form, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            .then(resp => {
                store.currentSessionId = resp.data.session_id
                store.chatHistory = []
                console.log('File uploaded for chat, session ID:', resp.data.session_id)
                // For TLOG files, use frontend parsing like the original repo
                if (isTlogFile) {
                    console.log('TLOG file detected - using frontend parsing for visualization')
                    // Set logType so Home.vue uses MavlinkDataExtractor
                    this.state.logType = 'tlog'
                    const reader = new FileReader()
                    reader.onload = () => {
                        worker.postMessage({
                            action: 'parse',
                            file: reader.result,
                            isTlog: true,
                            isDji: false
                        })
                    }
                    reader.readAsArrayBuffer(file)
                }
            })
            .catch(err => {
                console.error('Upload failed for chat:', err)
                alert('Log upload failed – see console')
            })
            // Always do frontend parsing for visualization (backend is just for chat)
            if (!isTlogFile) {
                const reader = new FileReader()
                reader.onload = () => {
                    worker.postMessage({
                        action: 'parse',
                        file: reader.result,
                        isTlog: false,
                        isDji: file.name.endsWith('txt')
                    })
                }
                reader.readAsArrayBuffer(file)
            }
        },
        async handleTlogVisualization (uploadResponse) {
            try {
                // Set logType to 'tlog' so Home.vue uses MavlinkDataExtractor
                this.state.logType = 'tlog'
                // Fetch the parsed data from backend for visualization
                const response = await axios.get(`/api/tlog-data/${uploadResponse.session_id}`)
                const backendData = response.data
                // Convert backend data to frontend format for Cesium
                const convertedData = this.convertBackendDataForCesium(backendData)
                // Also emit available message types for TLOG files
                const messageTypes = this.createMessageTypesStructure(convertedData)
                this.$eventHub.$emit('messageTypes', messageTypes)
                // Initialize with GPS data if available
                if (messageTypes.GPS || messageTypes.GPS_RAW_INT || Object.keys(messageTypes).length > 0) {
                    const firstMessageType = messageTypes.GPS
                        ? 'GPS'
                        : messageTypes.GPS_RAW_INT
                            ? 'GPS_RAW_INT'
                            : Object.keys(messageTypes)[0]
                    this.$eventHub.$emit('loadType', firstMessageType)
                }
                // Create metadata with startTime for Cesium
                const metadata = this.createTlogMetadata(convertedData)
                this.state.metadata = metadata
                // Emit to components that expect parsed data
                this.$eventHub.$emit('metadata', metadata)
                this.$eventHub.$emit('messagesDoneLoading')
                this.$eventHub.$emit('messages')
                console.log('TLOG visualization data ready:', convertedData)
                console.log('GPS data count:',
                    convertedData.GPS_RAW_INT ? convertedData.GPS_RAW_INT.time_boot_ms.length : 0)
                console.log('Available message types:', Object.keys(messageTypes))
            } catch (error) {
                console.error('Failed to fetch TLOG data for visualization:', error)
                // Initialize empty messages structure for fallback
                this.state.messages = {
                    GPS_RAW_INT: {
                        // eslint-disable-next-line camelcase
                        time_boot_ms: [],
                        lat: [],
                        lon: [],
                        alt: []
                    },
                    FMTU: []
                }
                // Emit empty message types to prevent UI errors
                this.$eventHub.$emit('messageTypes', {
                    GPS_RAW_INT: {
                        expressions: ['lat', 'lon', 'alt'],
                        complexFields: {
                            lat: { name: 'lat', type: 'number' },
                            lon: { name: 'lon', type: 'number' },
                            alt: { name: 'alt', type: 'number' }
                        }
                    }
                })
                this.$eventHub.$emit('loadType', 'GPS_RAW_INT')
                // Fallback: emit basic events so UI doesn't break
                const fallbackMetadata = { startTime: new Date(2015, 2, 25, 16) }
                this.state.metadata = fallbackMetadata
                this.$eventHub.$emit('metadata', fallbackMetadata)
                this.$eventHub.$emit('messagesDoneLoading')
                this.$eventHub.$emit('messages')
            }
        },
        convertBackendDataForCesium (backendData) {
            // Convert backend DataFrame format to frontend message format
            // This is where we'd map global_position_int messages to GPS format
            const messages = {
                FMTU: [] // Add FMTU to prevent 'in' operator errors
            }
            // Initialize state.messages if it doesn't exist
            if (!this.state.messages) {
                this.state.messages = {}
            }
            if (backendData && backendData.length > 0) {
                // Group data by message type
                const messageGroups = {}
                const gpsDataArray = [] // Collect GPS data first

                backendData.forEach(row => {
                    const msgType = row.msg_type || 'UNKNOWN'
                    if (!messageGroups[msgType]) {
                        messageGroups[msgType] = []
                    }
                    if (msgType === 'GLOBAL_POSITION_INT') {
                        // Convert to GPS format for Cesium
                        const gpsData = {
                            lat: row.lat / 10000000, // Convert from int32 to degrees
                            lon: row.lon / 10000000,
                            alt: row.alt / 1000, // Convert from mm to m
                            // eslint-disable-next-line camelcase
                            relative_alt: row.relative_alt / 1000,
                            // eslint-disable-next-line camelcase
                            time_boot_ms: row.time_boot_ms,
                            _timestamp: row._timestamp || row.TimeUS / 1000000,
                            TimeUS: row.TimeUS || row.time_boot_ms * 1000,
                            GWk: row.GWk || 0,
                            GMS: row.GMS || 0
                        }
                        gpsDataArray.push(gpsData)
                    } else if (msgType === 'GPS_RAW_INT') {
                        // Convert GPS_RAW_INT to GPS format for Cesium
                        console.log('Processing GPS_RAW_INT message:', row)
                        const gpsData = {
                            lat: row.lat / 10000000, // Convert from int32 to degrees
                            lon: row.lon / 10000000,
                            alt: row.alt / 1000, // Convert from mm to m
                            // eslint-disable-next-line camelcase
                            time_boot_ms: row.time_usec / 1000, // Convert microseconds to milliseconds
                            // eslint-disable-next-line camelcase
                            fix_type: row.fix_type,
                            // eslint-disable-next-line camelcase
                            satellites_visible: row.satellites_visible,
                            _timestamp: row._timestamp || row.time_usec / 1000000,
                            // Add fields expected by datetools.js
                            TimeUS: row.time_usec,
                            GWk: row.GWk || 0, // GPS week number (might be 0 for GPS_RAW_INT)
                            GMS: row.GMS || 0 // GPS milliseconds (might be 0 for GPS_RAW_INT)
                        }
                        console.log('Converted GPS data:', gpsData)
                        gpsDataArray.push(gpsData)
                    } else {
                        // Keep other message types as-is
                        messageGroups[msgType].push(row)
                    }
                })
                // Convert GPS data from array of objects to object of arrays (mavlink format)
                if (gpsDataArray.length > 0) {
                    const gpsStructure = {
                        // eslint-disable-next-line camelcase
                        time_boot_ms: [],
                        lat: [],
                        lon: [],
                        alt: [],
                        // eslint-disable-next-line camelcase
                        fix_type: [],
                        // eslint-disable-next-line camelcase
                        satellites_visible: [],
                        _timestamp: [],
                        TimeUS: [],
                        GWk: [],
                        GMS: []
                    }
                    gpsDataArray.forEach(gpsData => {
                        // eslint-disable-next-line camelcase
                        gpsStructure.time_boot_ms.push(gpsData.time_boot_ms)
                        gpsStructure.lat.push(gpsData.lat)
                        gpsStructure.lon.push(gpsData.lon)
                        gpsStructure.alt.push(gpsData.alt)
                        // eslint-disable-next-line camelcase
                        gpsStructure.fix_type.push(gpsData.fix_type || 0)
                        // eslint-disable-next-line camelcase
                        gpsStructure.satellites_visible.push(gpsData.satellites_visible || 0)
                        gpsStructure._timestamp.push(gpsData._timestamp)
                        gpsStructure.TimeUS.push(gpsData.TimeUS)
                        gpsStructure.GWk.push(gpsData.GWk)
                        gpsStructure.GMS.push(gpsData.GMS)
                    })
                    // Store as GPS_RAW_INT for MavlinkDataExtractor to find
                    messages.GPS_RAW_INT = gpsStructure
                }
                // Add all message groups to messages object
                Object.keys(messageGroups).forEach(msgType => {
                    if (msgType === 'GLOBAL_POSITION_INT' || msgType === 'GPS_RAW_INT') {
                        // Already handled above as GPS
                        return
                    }
                    messages[msgType] = messageGroups[msgType]
                })
            }
            // Ensure we have at least basic message types to prevent errors
            if (!messages.FMTU) {
                messages.FMTU = []
            }
            // Set the converted data to state so Cesium can use it
            this.state.messages = messages
            return messages
        },
        createMessageTypesStructure (convertedData) {
            const messageTypes = {}

            // Create proper structure for each message type
            Object.keys(convertedData).forEach(msgType => {
                if ((msgType === 'GPS' || msgType === 'GPS_RAW_INT' || msgType === 'GLOBAL_POSITION_INT') &&
                    convertedData[msgType] &&
                    typeof convertedData[msgType] === 'object' &&
                    // eslint-disable-next-line camelcase
                    convertedData[msgType].time_boot_ms) {
                    // GPS message types have special array structure, not array of objects
                    const expressions = Object.keys(convertedData[msgType]).filter(key =>
                        key !== '_timestamp' && // Skip internal fields
                        key !== 'msg_type' && // Skip message type field
                        Array.isArray(convertedData[msgType][key]) && // GPS fields are arrays
                        convertedData[msgType][key].length > 0 && // Non-empty array
                        typeof convertedData[msgType][key][0] === 'number' && // Numeric array
                        !isNaN(convertedData[msgType][key][0]) // Valid number
                    )

                    messageTypes[msgType] = {
                        expressions: expressions,
                        complexFields: {}
                    }

                    // Add field metadata for complexFields
                    expressions.forEach(field => {
                        messageTypes[msgType].complexFields[field] = {
                            name: field,
                            type: 'number'
                        }
                    })
                } else if (convertedData[msgType] && convertedData[msgType].length > 0) {
                    // Regular message types (array of objects)
                    const sampleMessage = convertedData[msgType][0]
                    const expressions = Object.keys(sampleMessage).filter(key =>
                        key !== '_timestamp' && // Skip internal fields
                        key !== 'msg_type' && // Skip message type field
                        typeof sampleMessage[key] === 'number' && // Only include numeric fields for plotting
                        !isNaN(sampleMessage[key]) // Ensure it's a valid number
                    )

                    messageTypes[msgType] = {
                        expressions: expressions,
                        complexFields: {}
                    }

                    // Add field metadata for complexFields
                    expressions.forEach(field => {
                        messageTypes[msgType].complexFields[field] = {
                            name: field,
                            type: typeof sampleMessage[field]
                        }
                    })
                }
            })

            return messageTypes
        },
        createTlogMetadata (convertedData) {
            // Create metadata structure similar to what DataflashParser provides
            let startTime = null
            // Try to extract start time from GPS data
            if (convertedData.GPS_RAW_INT && convertedData.GPS_RAW_INT.time_boot_ms &&
                convertedData.GPS_RAW_INT.time_boot_ms.length > 0) {
                // Use first GPS timestamp to estimate start time
                const firstTimestamp = convertedData.GPS_RAW_INT.time_boot_ms[0]
                // Create a reasonable start time (current time minus the timestamp offset)
                startTime = new Date(Date.now() - firstTimestamp)
            } else if (convertedData.GLOBAL_POSITION_INT && convertedData.GLOBAL_POSITION_INT.time_boot_ms &&
                       convertedData.GLOBAL_POSITION_INT.time_boot_ms.length > 0) {
                const firstTimestamp = convertedData.GLOBAL_POSITION_INT.time_boot_ms[0]
                startTime = new Date(Date.now() - firstTimestamp)
            }
            // Fallback to a default date if no GPS data
            if (!startTime) {
                startTime = new Date(2015, 2, 25, 16) // Default date used in CesiumViewer
            }
            return {
                startTime: startTime
            }
        },
        uploadFile () {
            this.uploadStarted = true
            this.transferMessage = 'Upload Done!'
            this.uploadpercentage = 0
            const formData = new FormData()
            formData.append('file', this.file)

            const request = new XMLHttpRequest()
            request.onload = () => {
                if (request.status >= 200 && request.status < 400) {
                    this.uploadpercentage = 100
                    this.url = request.responseText
                } else {
                    alert('error! ' + request.status)
                    this.uploadpercentage = 100
                    this.transferMessage = 'Error Uploading'
                    console.log(request)
                }
            }
            request.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    this.uploadpercentage = 100 * e.loaded / e.total
                }
            }
            , false)
            request.open('POST', '/upload')
            request.send(formData)
        },
        fixData (message) {
            if (message.name === 'GLOBAL_POSITION_INT') {
                message.lat = message.lat / 10000000
                message.lon = message.lon / 10000000
                // eslint-disable-next-line
                message.relative_alt = message.relative_alt / 1000
            }
            return message
        },
        browse () {
            document.getElementById('choosefile').click()
        },
        share () {
            const el = document.createElement('textarea')
            el.value = window.location.host + '/#/v/' + this.url
            document.body.appendChild(el)
            el.select()
            document.execCommand('copy')
            document.body.removeChild(el)
            this.shared = true
        },
        downloadFileFromURL (url) {
            const a = document.createElement('a')
            document.body.appendChild(a)
            a.style = 'display: none'
            a.href = url
            a.download = this.state.file + '-trimmed.' + this.state.logType
            a.click()
            document.body.removeChild(a)
            window.URL.revokeObjectURL(url)
        }
    },
    mounted () {
        window.addEventListener('message', (event) => {
            if (event.data.type === 'arrayBuffer') {
                worker.postMessage({
                    action: 'parse',
                    file: event.data.data,
                    isTlog: false,
                    isDji: false
                })
            }
        })
        worker.onmessage = (event) => {
            if (event.data.percentage) {
                this.state.processPercentage = event.data.percentage
            } else if (event.data.availableMessages) {
                this.$eventHub.$emit('messageTypes', event.data.availableMessages)
                // Initialize parser with GPS data after file is loaded
                if (this.state.logType === 'tlog') {
                    // For TLOG files, use GLOBAL_POSITION_INT or GPS_RAW_INT
                    if (event.data.availableMessages.GLOBAL_POSITION_INT) {
                        this.$eventHub.$emit('loadType', 'GLOBAL_POSITION_INT')
                    } else if (event.data.availableMessages.GPS_RAW_INT) {
                        this.$eventHub.$emit('loadType', 'GPS_RAW_INT')
                    }
                } else {
                    // For BIN files, use GPS
                    this.$eventHub.$emit('loadType', 'GPS')
                }
            } else if (event.data.metadata) {
                this.state.metadata = event.data.metadata
            } else if (event.data.messages) {
                this.state.messages = event.data.messages
                this.$eventHub.$emit('messages')
            } else if (event.data.messagesDoneLoading) {
                this.$eventHub.$emit('messagesDoneLoading')
            } else if (event.data.messageType) {
                this.state.messages[event.data.messageType] = event.data.messageList
                this.$eventHub.$emit('messages')
            } else if (event.data.files) {
                this.state.files = event.data.files
                this.$eventHub.$emit('messages')
            } else if (event.data.url) {
                this.downloadFileFromURL(event.data.url)
            }
        }
        const url = document.location.search.split('?file=')[1]
        if (url) {
            this.onLoadSample(decodeURIComponent(url))
        }
    },
    components: {
        VProgress
    }
}
</script>
<style scoped>

    /* NAVBAR */

    #drop_zone {
        padding-top: 25px;
        padding-left: 10px;
        border: 2px dashed #434b52da;
        width: auto;
        height: 100px;
        margin: 20px;
        border-radius: 5px;
        cursor: default;
        background-color: rgba(0, 0, 0, 0);
    }

    #drop_zone:hover {
        background-color: #171e2450;
    }

    .uploadCheckbox {
        margin-left: 20px;
    }

</style>
