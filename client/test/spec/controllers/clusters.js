'use strict';

describe('Controller: ClustersCtrl', function () {

  // load the controller's module
  beforeEach(module('svenClientApp'));

  var ClustersCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function ($controller, $rootScope) {
    scope = $rootScope.$new();
    ClustersCtrl = $controller('ClustersCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function () {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
