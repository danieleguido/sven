'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:CorpusCtrl
 * @description
 * # CorpusCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
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
      DocumentsFactory.save({
        id: $routeParams.id
      },{
        mimetype: 'text/html',
        date: $filter('date')($scope.document.date, 'dd/MM/yyyy'),//$scope.document.date,
        name: $scope.document.url
          .replace(/http:\/\/w+/g,'')
          .replace(/[^\w]/g, ' ')
          .replace(/\s+/g,' ')
          .trim().substring(0,64),
        url:$scope.document.url
      }, function(data) {
        console.log(data);
        data.object && $location.path('/document/' + data.object.id);
      });
    };

    $scope.openDatePicker = function($event) {
      $event.preventDefault();
      $event.stopPropagation();
      $scope.opened = true;
    };

    $scope.$on(API_PARAMS_CHANGED, function(){
      $log.debug('CorpusDocumentsCtrl @API_PARAMS_CHANGED');
      $scope.sync();
    });

    // start
    $scope.sync();
  })
