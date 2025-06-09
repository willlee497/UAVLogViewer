<template>
  <div id="app" style="height: 100%;">
    <!-- cache Home so it never re-initializes; ChatbotView will re-mount each time. -->
    <keep-alive include="Home">
      <router-view/>
    </keep-alive>
  </div>
</template>

<script>
export default {
    name: 'App'
}
</script>

<style>
@import url('https://fonts.googleapis.com/css?family=Nunito+Sans&display=swap');

html,
body,
#app,
#vuewrapper,
.container-fluid,
#wrapper,
#cesiumContainer {
    height: 100%;
    margin: 0;
    padding: 0;
}

#app {
    font-family: 'Nunito Sans', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

html,
body {
    overscroll-behavior-y: contain;
}
</style>
