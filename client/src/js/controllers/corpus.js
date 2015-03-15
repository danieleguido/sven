'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:CorpusCtrl
 * @description
 * # CorpusCtrl
 * Controller of the svenClientApp
 */
angular.module('sven')
  .controller('CorpusCtrl', function ($scope, $log, $routeParams, CorpusFactory) {
    $log.debug('CorpusCtrl ready ca');
    
    $scope.localCorpus = {};

    CorpusFactory.query({id: $routeParams.id}, function(data) {
      console.log(data)
      $scope.$parent.diffclone($scope.localCorpus, data.object);
    })
    
    $scope.$watch('corpora', function(){// pseudo react diff. looking for the local corpus among different corpora
      for(var i=0; i<$scope.$parent.corpora.length; i++) {
        if($scope.$parent.corpora[i].id == $routeParams.id) {
          $scope.$parent.diffclone($scope.localCorpus, $scope.$parent.corpora[i])
        }
      }
    });

  })
  /*
    Documents attached to a corpus.
    url corpus/<corpus_id>/documents

  */
  .controller('CorpusDocumentsCtrl', function ($scope, $filter, $log, $location, $routeParams, DocumentFactory, DocumentsFactory) {
    $log.debug('CorpusDocumentsCtrl ready');
    // reset orderby
    $scope.$parent.orderBy.choices = [
        {label:'by date added', value:'-date_created'},
        {label:'by date', value:'date'},
        {label:'by name', value:'name'}
      ];
    $scope.$parent.orderBy.choice = $scope.$parent.orderBy.choices[0];
    

    $scope.document = {
      date: new Date()
    };  

    $scope.sync = function() {
      DocumentsFactory.query(
        $scope.getParams({
          id:$routeParams.id
        }),
        function(data) {
          $log.info('loading documents', data);
          $scope.totalItems = data.meta.total_count;
          $scope.items = data.objects;
        },
        function(){}
      );
    };

    $scope.remove = function(doc) {
      if(confirm('Do you really want to remove the document "'+doc.name+'"?')) {
        DocumentFactory.remove({id:doc.id}, function(res){
          console.log(res);
          if(res.status == 'ok') {
            toast('document "' + doc.name +'" removed correctly');
          }
          $scope.sync();
        });
      } // end if
    };

    $scope.saveUrl = function() {
      $log.info('saveUrl: ', $scope.document.url);
      var doc = {
        mimetype: 'text/html',
        date: $filter('date')($scope.document.date, 'yyyy-MM-dd'),//$scope.document.date,
        name: $scope.document.url
          .replace(/http:\/\/w+/g,'')
          .replace(/[^\w]/g, ' ')
          .replace(/\s+/g,' ')
          .trim().substring(0,64),
        url:$scope.document.url
      }

      if($scope.document.__url_type && $scope.document.__url_type.length) {
        doc.tags = [
          {
            type: 'tm',
            tags:[
              $scope.document.__url_type
            ]
          }
        ];
      }

      DocumentsFactory.save({
        id: $routeParams.id
      },doc, function(data) {
        console.log(data);
        data.object && $location.path('/document/' + data.object.id);
      });
    };


    $scope.openDatePicker = function($event) {
      $event.preventDefault();
      $event.stopPropagation();
      $scope.opened = true;
    };

    /*
      Export current corpus in a single csv file
    */
    $scope.exportCorpus = function() {
      $log.debug('CorpusDocumentsCtrl --> exportCorpus()');
      window.open(SVEN_BASE_URL + '/api/export/corpus/' + $routeParams.id + '/document?filters=' + JSON.stringify($scope.filters), '_blank', '');
    //ng-href="/api/export/corpus/{{corpus.id}}/document?filters={{filters|json}}"
    };

    var api_params_changed_timer = 0;
    $scope.$on(API_PARAMS_CHANGED, function(){
      $log.info('CorpusDocumentsCtrl @API_PARAMS_CHANGED, waiting 300ms...');
      api_params_changed_timer && clearTimeout($scope.api_params_changed);
      api_params_changed_timer = setTimeout(function() {
        $log.info('CorpusDocumentsCtrl @API_PARAMS_CHANGED executed');
      
        $scope.sync();
      }, 300);
    });

    // start
    $scope.sync();
  })
