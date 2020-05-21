// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'

import Vuetify from 'vuetify'
import 'vuetify/dist/vuetify.css'
import 'leaflet/dist/leaflet.css'

import App from './App'
import router from './router'
import store from './store'

Vue.use(Vuetify)

const vuetifyOptions = { }

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store,
  template: '<App/>',
  components: { App },
  vuetify: new Vuetify(vuetifyOptions),
  beforeCreate() {
    this.$store.dispatch('init');
	}
})
