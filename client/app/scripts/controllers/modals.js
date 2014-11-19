'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:StopwordsCtrl
 * @description
 * # ModalTagCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('AttachTagCtrl', function ($scope, $modalInstance, item) {
    $scope.item = item;

    $scope.ok = function () {
      $modalInstance.close();
    };

    $scope.cancel = function () {
      $modalInstance.dismiss('cancel');
    };
  })
  

  .controller('ModalTagCtrl', function ($scope, $routeParams, $log, $modal) {
    

    var attachtag;

    $scope.$on(OPEN_ATTACH_TAG, function(e,doc) {
      attachtag = $modal.open({
        templateUrl: 'myModalContent.html',
        controller: 'AttachTagCtrl',
        backdrop:false,
        size: 'sm',
        resolve: {
          item: function () {
            return doc;
          }
        }
      });
    });
  })


  .controller('PreviewTsvCtrl', function ($scope, $modalInstance, table) {
    $scope.table = table;

    $scope.ok = function () {
      $modalInstance.close();
      $scope.onMetadataStart();
    };

    $scope.cancel = function () {
      $modalInstance.dismiss('cancel');
    };
  })
  .controller('ModalPreviewTsvCtrl', function ($scope, $filter, $routeParams, $log, $modal) {
    var modal;

    $scope.$watch('tsv', function(tsv) {
      if(!tsv)
        return;
      modal = $modal.open({
        templateUrl: 'previewTsv.html',
        controller: 'PreviewTsvCtrl',
        backdrop:false,
        resolve: {
          table: function () {
            console.log()
            return $filter('tsv')(tsv);
          }
        }
      });
    });
  })
  ;