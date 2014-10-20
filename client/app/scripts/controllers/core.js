'use strict';

var API_PARAMS_CHANGED = 'api_params_changed';


function toast(message, title, options){
  if(!options){
    options={}
  };
  if(typeof title=="object"){
    options=title;
    title=undefined;
  }

  if(options.cleanup!=undefined)
    $().toastmessage("cleanToast");
  var settings=$.extend({
    text: "<div>"+(!title?"<h1>"+message+"</h1>":"<h1>"+title+"</h1><p>"+message+"</p>")+"</div>",
    type: "notice",
    position: "bottom-center",
    inEffectDuration: 200,
    outEffectDuration: 200,
    stayTime: 1900
  },options);

  $().toastmessage("showToast", settings);
};

/**
 * @ngdoc function
 * @name svenClientApp.controller:CoreCtrl
 * @description
 * # CoreCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('CoreCtrl', function ($scope, $log, $upload, $sce, $cookies, $timeout, LoginFactory, CommandFactory, NotificationFactory) {
    $log.debug('CoreCtrl ready');
    $scope.status = 'LOADING';

    
    // current corpus
    $scope.corpus = {};

    // current user
    $scope.profile = {};

    // available corpora
    $scope.corpora = [];

    // current jobs
    $scope.jobs = [];

    // current pagination page
    $scope.page = 1;

    // limit result per page
    $scope.limit = 50;

    // offset result per page, internal use
    $scope.offset = 0;

    // number of items for pagination purpose
    $scope.totalItems = 0;

    // current documents filters (tags, language, date)
    $scope.filters = {};
    $scope.filtersItems = {}; // the collection of actual emlement in order not to reload every time filters vars

    $scope.now = new Date(); // today datetime

    // current documents orderby(s). Watch for $scope.$watch('orderBy.choice') 
    $scope.orderBy = {
      choices: [
        {label:'by date added', value:'-date_created'},
        {label:'by date', value:'date'},
        {label:'by name', value:'name'}
      ],
      choice: {label:'by date added', value:'-date_created'},
      isopen: false,
      direction: true // a-z or false z-a
    };

    // getting the corpus id via cookie
    var corpusId = $cookies.corpusId;

    /*
      Clone source in target by changing only the different fields
    */
    $scope.diffclone = function(target, source) {
      if(!target) {
        target = source;
      } else {
        for(var i in source) {
          if(typeof target[i]=='object') {
            $scope.diffclone(target[i], source[i]);
          } else if(!target[i] || target[i] != source[i]) {//console.log('updtargetted', i);
            target[i] = source[i];
          }
        }
      }
    };


    $scope.html = function(html_code) {
      return $sce.trustAsHtml(html_code);
    }


    function tick() {
      NotificationFactory.query({},function(data){
        //todo jobs diff
        
        
        if(data.meta.profile.date_last_modified != $scope.profile.date_last_modified)
          $scope.profile = data.meta.profile;

        //$scope.profile.documents = data.objects.reduce(function(a,b){ return a.count.documents + b.count.documents })
        // check if differences
        $scope.diffclone($scope.corpora, data.objects);
        $scope.jobs = data.jobs;
        // if corpusID choose the corpus matching corpusId, if any. @todo
        var candidate = data.objects[data.objects.length-1];
        for(var i=0; i<data.objects.length;i++) {
          if($cookies.corpusId == data.objects[i].id)
            candidate = data.objects[i];
        }
        $scope.diffclone($scope.corpus, candidate);
        
        // update status and do things
        
        if(data.status != "ok" && data.code=='Unauthorized') {
          $scope.status = 'Unauthorized';
        } else {
          $scope.status = 'RUNNING';
        };
        //$scope.corpus = candidate;
        
        $timeout(tick, 4617);
        
      }, function(data){
        $log.error('ticking error',data); // status 500 or 404 or other stuff
        $timeout(tick, 4917);
        $scope.status = 'ERROR';

      }); /// todo HANDLE correctly connection refused
    };
    
    $timeout(tick, 517);

    /*
      handle file upload at upper level
    */
    $scope.uploadingQueue = [];
    var uploaders = {};
    
    var start = function($file, index) {
      uploaders[index] = $upload.upload({
          url: '/api/corpus/' + $scope.corpus.id + '/upload', //upload.php script, node.js route, or servlet url
          file: $file
        }).then(function(res) {
          $scope.uploadingQueue[index].completion = 100;
          console.log(res);
          $log.info('completed', res);
          toast('uploading completed', $scope.uploadingQueue[index].name);
        }, function(response) {
          $log.error(response);
          //if (response.status > 0) $scope.errorMsg = response.status + ': ' + response.data;
        }, function(evt) {
          // Math.min is to fix IE which reports 200% sometimes
          $scope.uploadingQueue[index].completion = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
        });
    };

    $scope.onFileSelect = function($files) {
      $log.debug('onFileSelect', $files);
      $scope.uploadingQueue = [];
      uploaders = {};
      toast('uploading ' + $files.length + ' files...');
      
      for ( var i = 0; i < $files.length; i++) {
        var $file = $files[i];
        $scope.uploadingQueue.push({
          size: $file.size,
          name: $file.name,
          type: $file.type,
          index: i,
          completion: 0
        });
        start($file, i);
        
      }
    };

    
    $scope.changePage = function(page){
      $log.info('changePage', page);
      $scope.page = page;
      $scope.$broadcast(API_PARAMS_CHANGED);
    };


    $scope.changeFilter = function(key, filter, item) {
      $scope.filters[key] = filter;
      $scope.filtersItems[key] = angular.extend({
        filter: filter
      }, item);
      $scope.$broadcast(API_PARAMS_CHANGED);
    };

    $scope.removeFilter = function(key, filter) {
      if($scope.filters[key] == filter) {
        delete $scope.filters[key];
        delete $scope.filtersItems[key];
      };

      $scope.$broadcast(API_PARAMS_CHANGED);
    };
    /*
      Orderby set
    */
    $scope.changeOrderBy = function(choice) {
      $log.info('changeOrderBy', choice);
      $scope.page = 1;
      $scope.orderBy.choice = choice;
      $scope.orderBy.isopen = false;
      $scope.$broadcast(API_PARAMS_CHANGED);
    };

    /*
      return a dict object that can be used to call 'glue' api.
      it handles: filters, order_by, search, limit and offset
      according to pagination.
    */
    $scope.getParams = function(params) {
      var params = angular.extend({
        offset: $scope.limit * ($scope.page - 1),
        limit: $scope.limit,
        filters: JSON.stringify(angular.copy($scope.filters)),
        order_by: JSON.stringify($scope.orderBy.choice.value.split('|'))
      }, params);
      return params;
    };


    /*
      Call the right api to execute the desired command.
      For a list of all available cmd please cfr. ~/sven/management/start_job.py
      @param cmd - a valid cmd command to be passed to api/start. Cfr api.py
      @param corpus - <Corpus> as command target
    */
    $scope.executeCommand = function(cmd, corpus) {
      CommandFactory.launch({
        id: corpus.id,
        cmd: cmd
      }, function(res) {
        if(res.status=="ok")
          toast('command started');
      })
    };


    /*
      change the main corpus cookie, enabling upload on it.
    */
    $scope.activate = function(corpus) {
      $cookies.corpusId = corpus.id;
      toast('activating corpus ...');
    }


    /*
      handle corpus management
    */
    $scope.$watch('corpus', function(){
      if(!$scope.corpus.id || corpusId == $scope.corpus.id)
        return;
      corpusId = $scope.corpus.id; // set cookie please...
      console.log('switch to corpus:', $scope.corpus.name);
    })
    $log.info('corpus id (cookies):', corpusId || 'cookie not set');
  });
